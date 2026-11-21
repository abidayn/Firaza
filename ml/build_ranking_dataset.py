"""P1.4 - Build the learning-to-rank training table.

One row = one (simulated request, candidate vendor) pair.
Features come from backend/app/core/features.py (same code the app uses).
Labels (0-4) come from a utility function that uses the HIDDEN truth
(reliability_true, quality_true) which the model never sees directly.

Run from the repo root:  .venv/Scripts/python ml/build_ranking_dataset.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.features import FEATURE_NAMES, build_candidate_features, clean_transactions, history_stats  # noqa: E402

DATA = ROOT / "ml" / "data"
SEED = 42
N_REQUESTS = 3000
QTYS = [20, 50, 100, 200, 500]
DEADLINES = [1, 2, 3, 5, 7, 10]
DEADLINE_P = [0.10, 0.20, 0.25, 0.25, 0.12, 0.08]   # weighted toward 2-5 days


def utility(f: pd.DataFrame, truth: pd.DataFrame, req: dict, rng) -> np.ndarray:
    """Ground-truth 'how good is this vendor for this request', from hidden truth + offer terms."""
    t = truth.set_index("vendor_id").reindex(f.index)
    rel, q_true = t["reliability_true"].to_numpy(), t["quality_true"].to_numpy()
    p = f["unit_price_eff"].to_numpy()
    price_s = 1 - (p - p.min()) / (p.max() - p.min()) if p.max() > p.min() else np.ones_like(p)
    lead = f["lead_typ"].to_numpy()
    deadline = req["deadline_days"]
    slack_s = np.clip((deadline - lead + 3) / 6, 0, 1)
    qual_s = np.sqrt(np.clip((q_true - 1) / 4, 0, 1))            # diminishing returns on quality
    speed_s = 0.6 * slack_s + 0.4 * rel
    u = req["w_price"] * price_s + req["w_speed"] * speed_s + req["w_quality"] * qual_s
    if deadline <= 2:
        u = u - 0.25 * (1 - rel)                                  # urgent orders punish unreliable vendors
    u = u - 0.30 * (lead > deadline)                              # hard deadline miss
    u = u - 0.20 * (f["moq_ratio"].to_numpy() > 1)                # order below the vendor's MOQ
    u = u - 0.15 * (f["in_stock"].to_numpy() == 0)                # out of stock
    return u + rng.normal(0, 0.04, len(u))                        # judgement noise


def to_labels(u: np.ndarray) -> np.ndarray:
    span = u.max() - u.min()
    u_norm = (u - u.min()) / span if span > 0 else np.zeros_like(u)
    return np.minimum(4, np.floor(u_norm * 5)).astype(int)


def main() -> None:
    rng = np.random.default_rng(SEED)
    vm = pd.read_csv(DATA / "vendor_materials.csv")
    tx = clean_transactions(pd.read_csv(DATA / "transactions.csv"))
    truth = pd.read_csv(DATA / "_latent" / "vendor_truth.csv")
    stats = history_stats(tx)
    materials = sorted(vm["material_id"].unique())

    frames = []
    for rid in range(1, N_REQUESTS + 1):
        w = rng.dirichlet([1, 1, 1])
        req = {"material_id": int(rng.choice(materials)), "qty": int(rng.choice(QTYS)),
               "deadline_days": int(rng.choice(DEADLINES, p=DEADLINE_P)),
               "w_price": float(w[0]), "w_speed": float(w[1]), "w_quality": float(w[2])}
        f = build_candidate_features(req, vm, tx, stats=stats)
        f["label"] = to_labels(utility(f, truth, req, rng))
        f["request_id"] = rid
        frames.append(f.reset_index())

    data = pd.concat(frames, ignore_index=True)
    ids = rng.permutation(N_REQUESTS) + 1
    n_train, n_val = int(0.70 * N_REQUESTS), int(0.15 * N_REQUESTS)
    split = {i: "train" for i in ids[:n_train]}
    split.update({i: "val" for i in ids[n_train:n_train + n_val]})
    split.update({i: "test" for i in ids[n_train + n_val:]})
    data["split"] = data["request_id"].map(split)
    data = data[["request_id", "split", "vendor_id", *FEATURE_NAMES, "label"]]
    data.to_csv(DATA / "ranking_train.csv", index=False)

    sizes = data.groupby("request_id").size()
    print(f"rows={len(data)} requests={data.request_id.nunique()} candidates/request min={sizes.min()} max={sizes.max()}")
    print("label counts:", data["label"].value_counts().sort_index().to_dict())
    print("split requests:", data.groupby("split")["request_id"].nunique().to_dict())
    assert data.groupby("request_id")["split"].nunique().max() == 1, "a request leaked across splits"


if __name__ == "__main__":
    main()
