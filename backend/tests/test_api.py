"""API tests on a fresh SQLite database (seeded from ml/data). Gemini is mocked."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app import services
from app.core.features import FEATURE_NAMES
from app.db import Base, get_db, make_engine, normalize_url
from app.main import app
from app.rag import explain as explain_mod


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = make_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", Session)
    monkeypatch.setattr(services, "engine", engine)
    monkeypatch.setattr("app.main.SessionLocal", Session)
    Base.metadata.create_all(engine)
    with Session() as s:
        services.seed_if_empty(s)

    def _db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


REQ = {"material_id": 1, "qty": 100, "deadline_days": 3, "w_price": 0.3, "w_speed": 0.5, "w_quality": 0.2}


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is True


def test_vendor_crud_round_trip(client):
    created = client.post("/api/v1/vendors", json={"name": "CV Uji Coba", "city": "Bandung"}).json()
    vid = created["id"]
    assert client.get(f"/api/v1/vendors/{vid}").json()["name"] == "CV Uji Coba"
    assert client.put(f"/api/v1/vendors/{vid}", json={"name": "CV Uji Dua", "city": "Solo"}).json()["city"] == "Solo"
    assert client.delete(f"/api/v1/vendors/{vid}").status_code == 204
    assert client.get(f"/api/v1/vendors/{vid}").status_code == 404


def test_delete_vendor_with_offers_is_blocked(client):
    assert client.delete("/api/v1/vendors/1").status_code == 409


def test_duplicate_vendor_name_conflict(client):
    name = client.get("/api/v1/vendors/1").json()["name"]
    assert client.post("/api/v1/vendors", json={"name": name}).status_code == 409


def test_recommendation_order_and_flags(client):
    r = client.post("/api/v1/recommendations", json=REQ)
    assert r.status_code == 201
    results = r.json()["results"]
    assert len(results) >= 5
    scores = [x["score"] for x in results]
    assert scores == sorted(scores, reverse=True)
    assert [x["rank"] for x in results] == list(range(1, len(results) + 1))
    for x in results:
        assert x["misses_deadline"] == (x["lead_time_days"] > REQ["deadline_days"])
        assert set(x["contributions"]) == set(FEATURE_NAMES)
    saved = client.get(f"/api/v1/recommendations/{r.json()['request_id']}").json()
    assert [x["vendor_id"] for x in saved["results"]] == [x["vendor_id"] for x in results]


def test_invalid_payloads(client):
    assert client.post("/api/v1/recommendations", json={**REQ, "qty": 0}).status_code == 422
    assert client.post("/api/v1/recommendations", json={**REQ, "deadline_days": 99}).status_code == 422
    zero = {**REQ, "w_price": 0, "w_speed": 0, "w_quality": 0}
    assert client.post("/api/v1/recommendations", json=zero).status_code == 422
    assert client.post("/api/v1/recommendations", json={**REQ, "material_id": 999}).status_code == 404


def test_explanation_fallback_when_llm_down(client, monkeypatch):
    def down(*_a, **_k):
        raise explain_mod.LLMUnavailable("down")
    monkeypatch.setattr(explain_mod, "ensure_kb", lambda db: 0)
    monkeypatch.setattr(explain_mod, "retrieve", lambda rec: [])
    monkeypatch.setattr(explain_mod, "generate", down)
    rid = client.post("/api/v1/recommendations", json=REQ).json()["request_id"]
    e = client.post(f"/api/v1/recommendations/{rid}/explanation").json()
    assert e["source"] == "fallback" and "direkomendasikan" in e["text"]


def test_explanation_llm_success_and_cache(client, monkeypatch):
    calls = []

    def fake_generate(prompt, system):
        calls.append(1)
        return "Vendor teratas direkomendasikan karena paling seimbang.", "fake-model"
    monkeypatch.setattr(explain_mod, "ensure_kb", lambda db: 0)
    monkeypatch.setattr(explain_mod, "retrieve", lambda rec: [{"id": "policy-x", "text": "contoh"}])
    monkeypatch.setattr(explain_mod, "generate", fake_generate)
    rid = client.post("/api/v1/recommendations", json=REQ).json()["request_id"]
    first = client.post(f"/api/v1/recommendations/{rid}/explanation").json()
    second = client.post(f"/api/v1/recommendations/{rid}/explanation").json()
    assert first["source"] == "llm" and first["sources"] == ["policy-x"]
    assert second["text"] == first["text"] and len(calls) == 1


def test_invented_number_triggers_unverified_fallback(client, monkeypatch):
    monkeypatch.setattr(explain_mod, "ensure_kb", lambda db: 0)
    monkeypatch.setattr(explain_mod, "retrieve", lambda rec: [])
    monkeypatch.setattr(explain_mod, "generate", lambda p, s: ("Hemat Rp 987.654 bila memilih vendor ini.", "fake"))
    rid = client.post("/api/v1/recommendations", json=REQ).json()["request_id"]
    e = client.post(f"/api/v1/recommendations/{rid}/explanation").json()
    assert e["source"] == "fallback_unverified"


def test_verify_numbers():
    ctx = "total Rp 148.000, tepat waktu 69%, kualitas 3.2/5"
    assert explain_mod.verify_numbers("Total Rp 148.000 dan tepat waktu 69%. (1) (2)", ctx)
    assert not explain_mod.verify_numbers("Total Rp 150.000", ctx)


def test_neon_url_rewrite():
    url, args = normalize_url("postgresql://u:p@ep-x.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    assert url == "postgresql+pg8000://u:p@ep-x.ap-southeast-1.aws.neon.tech/neondb"
    assert args == {"ssl_context": True}
