"""Home page of the Firaza Vendor Recommendation & Procurement Assistant."""
import pandas as pd
import streamlit as st

from app_core import services, session, setup, status

setup("Beranda")

st.title("Firaza · Asisten Rekomendasi Vendor")
st.write(
    "Aplikasi decision-support untuk procurement Firaza. Masukkan kebutuhan material, lalu **model ranking "
    "(LightGBM LambdaRank)** mengurutkan vendor berdasarkan harga, kecepatan, kualitas, dan histori transaksi. "
    "**RAG** (Gemini embedding + vector store + Gemini) kemudian menjelaskan alasan dan trade-off-nya. "
    "Keputusan akhir tetap di tangan owner atau karyawan."
)

s = status()
c1, c2, c3 = st.columns(3)
c1.metric("Model ranking", "Siap" if s["model_loaded"] else "Tidak termuat")
c2.metric("Penjelasan AI", "Gemini aktif" if s["llm_configured"] else "Mode template")
c3.metric("Vector store", s["vector_store"])

with session() as db:
    n = services.counts(db)
    recent = services.recent_requests(db, 5)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vendor", n["vendors"])
c2.metric("Material", n["materials"])
c3.metric("Penawaran vendor", n["vendor_materials"])
c4.metric("Transaksi", n["transactions"])

st.subheader("Cara pakai")
st.markdown(
    "1. Buka **Rekomendasi Vendor**, pilih material, jumlah, tenggat, dan prioritas.\n"
    "2. Lihat urutan vendor, perbandingan harga, dan faktor yang paling memengaruhi skor.\n"
    "3. Baca penjelasan AI tentang alasan rekomendasi dan risikonya.\n"
    "4. Kelola data di halaman **Vendor**, **Material & Harga**, dan **Transaksi**."
)

if recent:
    st.subheader("Permintaan terakhir")
    st.dataframe(pd.DataFrame(recent).rename(columns={
        "request_id": "ID", "material": "Material", "qty": "Jumlah", "deadline_days": "Tenggat (hari)",
        "created_at": "Waktu"}), hide_index=True, width="stretch")

st.caption("Prototipe capstone Dicoding Bootcamp Batch 15 · Data sintetis, bukan data asli Firaza.")
