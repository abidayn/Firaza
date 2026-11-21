"""The main page: procurement need -> ranked vendors -> AI explanation."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app_core import models, pct, rp, services, session, setup, show_error

setup("Rekomendasi Vendor")
st.title("Rekomendasi Vendor")
st.caption("Model ranking mengurutkan vendor; RAG + Gemini menjelaskan alasannya.")

FEATURE_WORDS = {
    "unit_price_eff": "Harga satuan", "price_rel_median": "Harga vs vendor lain", "lead_typ": "Lama pengiriman",
    "slack_typ": "Sisa waktu ke tenggat", "lead_p90": "Pengiriman terlama (histori)",
    "slack_p90": "Sisa waktu (histori terburuk)", "quality_score": "Skor kualitas", "ontime_rate": "Ketepatan waktu",
    "defect_rate": "Tingkat cacat", "moq_ratio": "Minimum order (MOQ)", "in_stock": "Stok tersedia",
    "n_tx": "Jumlah histori", "deadline_days": "Tenggat", "log_qty": "Jumlah pesanan",
}

with session() as db:
    materials = services.list_rows(db, models.Material)
mat_names = {m.id: f"{m.name} ({m.unit})" for m in materials}

with st.form("need"):
    c1, c2, c3 = st.columns([2, 1, 1])
    material_id = c1.selectbox("Material", list(mat_names), format_func=mat_names.get)
    qty = c2.number_input("Jumlah", min_value=1, max_value=100000, value=100, step=10)
    deadline = c3.number_input("Tenggat (hari)", min_value=1, max_value=30, value=3)
    st.write("Prioritas (geser sesuai kebutuhan; akan dinormalisasi otomatis)")
    c1, c2, c3 = st.columns(3)
    w_price = c1.slider("Harga murah", 0, 100, 30, 5)
    w_speed = c2.slider("Cepat & tepat waktu", 0, 100, 50, 5)
    w_quality = c3.slider("Kualitas", 0, 100, 20, 5)
    go = st.form_submit_button("Cari rekomendasi", type="primary")

if go:
    try:
        with session() as db:
            st.session_state["rec"] = services.recommend(db, material_id, int(qty), int(deadline),
                                                         w_price / 100, w_speed / 100, w_quality / 100)
    except Exception as exc:
        st.session_state.pop("rec", None)
        show_error(exc)

rec = st.session_state.get("rec")
if rec:
    res = rec["results"]
    top = res[0]
    st.success(f"Rekomendasi utama: **{top['vendor_name']}** · total {rp(top['total_price'])} · "
               f"lead time {top['lead_time_days']} hari · tepat waktu {pct(top['ontime_rate'])}")

    table = pd.DataFrame([{
        "Peringkat": r["rank"], "Vendor": r["vendor_name"], "Skor (0-100)": r["score_pct"],
        "Harga satuan": rp(r["unit_price"]), "Total": rp(r["total_price"]), "Lead time (hari)": r["lead_time_days"],
        "Kualitas": r["quality_score"], "Tepat waktu": pct(r["ontime_rate"]),
        "Catatan": ", ".join(x for x, f in (("melewati tenggat", r["misses_deadline"]), ("di bawah MOQ", r["below_moq"]),
                                           ("stok kosong", not r["in_stock"])) if f) or "-",
    } for r in res])
    st.dataframe(table, hide_index=True, width="stretch")

    c1, c2 = st.columns(2)
    chart = pd.DataFrame({"Vendor": [f"#{r['rank']} {r['vendor_name']}" for r in res[:8]],
                          "Total harga": [r["total_price"] for r in res[:8]],
                          "Status": ["Rekomendasi" if r["rank"] == 1 else "Alternatif" for r in res[:8]]})
    fig = px.bar(chart, x="Total harga", y="Vendor", color="Status", orientation="h", title="Total harga (8 teratas)",
                 color_discrete_map={"Rekomendasi": "#534AB7", "Alternatif": "#B4B2A9"})
    fig.update_layout(yaxis={"categoryorder": "array", "categoryarray": chart["Vendor"][::-1]}, height=380)
    c1.plotly_chart(fig, width="stretch")

    contrib = sorted(((FEATURE_WORDS[k], v) for k, v in top["contributions"].items() if k in FEATURE_WORDS),
                     key=lambda kv: abs(kv[1]), reverse=True)[:6]
    cdf = pd.DataFrame(contrib, columns=["Faktor", "Pengaruh"])
    cdf["Arah"] = ["Menaikkan skor" if v > 0 else "Menurunkan skor" for v in cdf["Pengaruh"]]
    fig2 = px.bar(cdf, x="Pengaruh", y="Faktor", color="Arah", orientation="h",
                  title=f"Faktor terkuat untuk {top['vendor_name']} (dari model)",
                  color_discrete_map={"Menaikkan skor": "#1D9E75", "Menurunkan skor": "#D85A30"})
    fig2.update_layout(yaxis={"categoryorder": "array", "categoryarray": cdf["Faktor"][::-1]}, height=380)
    c2.plotly_chart(fig2, width="stretch")

    st.subheader("Penjelasan AI")
    with st.spinner("Mengambil dokumen pendukung dan menyusun penjelasan..."):
        try:
            from app.rag.explain import explain
            with session() as db:
                e = explain(db, rec)
        except Exception as exc:
            e = None
            show_error(exc)
    if e:
        label = {"llm": f"Dihasilkan Gemini ({e['model'].replace('models/', '')}) dari dokumen RAG",
                 "fallback": "Penjelasan template (Gemini tidak tersedia)",
                 "fallback_unverified": "Penjelasan template (teks AI gagal verifikasi angka)"}[e["source"]]
        st.info(e["text"])
        st.caption(label)
        if e["sources"]:
            with st.expander("Dokumen yang dipakai (retrieval)"):
                st.write(", ".join(e["sources"]))
    st.caption("Model hanya memberi saran. Keputusan akhir tetap di tangan owner atau karyawan.")
