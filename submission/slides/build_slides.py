"""Build the pitch deck (submission/slides/firaza_pitch.pptx) from the project's real results.

Run from the repo root:  .venv/Scripts/python submission/slides/build_slides.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "ml" / "reports"
OUT = Path(__file__).resolve().parent
PURPLE, DARK, GRAY, TEAL, LIGHT = (RGBColor(0x53, 0x4A, 0xB7), RGBColor(0x2C, 0x2C, 0x2A),
                                    RGBColor(0x5F, 0x5E, 0x5A), RGBColor(0x0F, 0x6E, 0x56), RGBColor(0xEE, 0xED, 0xFE))

metrics = json.loads((REPORTS / "metrics.json").read_text())
rag = json.loads((REPORTS / "rag_eval.json").read_text())

# chart: model vs baselines
names = {"lightgbm_lambdarank": "LightGBM\nLambdaRank", "baseline_weighted_sum": "Rumus bobot",
         "baseline_cheapest": "Termurah", "baseline_topsis": "TOPSIS", "control_shuffled_labels": "Kontrol\n(label acak)"}
fig, ax = plt.subplots(figsize=(7, 4))
vals = [metrics[k]["ndcg@3"] for k in names]
bars = ax.bar(list(names.values()), vals, color=["#534AB7", "#B4B2A9", "#B4B2A9", "#B4B2A9", "#D3D1C7"])
ax.axhline(0.85, color="#D85A30", ls="--", lw=1)
ax.text(4.4, 0.86, "target 0,85", color="#D85A30", ha="right", fontsize=9)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}".replace(".", ","), ha="center", fontsize=10)
ax.set_ylim(0, 1.05); ax.set_ylabel("NDCG@3 (data uji)"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "chart_ndcg.png", dpi=160); plt.close(fig)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def text(slide, x, y, w, h, s, size=20, bold=False, color=DARK):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(s if isinstance(s, list) else [s]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size, p.font.bold, p.font.color.rgb = Pt(size), bold, color
        p.space_after = Pt(8)
    return tb


def slide(title, section=None):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = PURPLE; bar.line.fill.background()
    if section:
        text(s, 0.6, 0.35, 8, 0.4, section.upper(), 12, True, PURPLE)
    text(s, 0.6, 0.65, 12, 0.9, title, 32, True)
    text(s, 0.6, 7.0, 12, 0.4, "Firaza · Vendor Recommendation & Procurement Assistant · DB15-I036", 10, False, GRAY)
    return s


def bullets(s, items, x=0.6, y=1.8, w=12, size=20):
    return text(s, x, y, w, 5, [f"•  {i}" for i in items], size)


def card(s, x, y, w, h, title, body, color=PURPLE):
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.color.rgb = color
    box.adjustments[0] = 0.08
    text(s, x + 0.2, y + 0.15, w - 0.4, 0.5, title, 18, True, color)
    text(s, x + 0.2, y + 0.75, w - 0.4, h - 0.9, body, 18)


def image(s, path, x, y, w=None, h=None):
    s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


# 1 title
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = PURPLE; bg.line.fill.background()
text(s, 0.9, 2.0, 11.5, 1.2, "Firaza · Asisten Rekomendasi Vendor", 44, True, RGBColor(255, 255, 255))
text(s, 0.9, 3.2, 11.5, 1.0, "Model ranking + RAG untuk procurement UMKM yang konsisten dan bisa dijelaskan", 22, False,
     RGBColor(0xEE, 0xED, 0xFE))
text(s, 0.9, 5.2, 11.5, 1.2, ["Abid Dayyan · b26b15a027 · Generative AI · Capstone individu DB15-I036",
                              "Dicoding Bootcamp Batch 15 · Use Case Firaza #3"], 16, False, RGBColor(255, 255, 255))

# 2 background
s = slide("Firaza: hampers & personalized gifts, 99% online", "a. Latar belakang")
bullets(s, ["Produk utama: handuk, sajadah custom, kado pernikahan; dijual di Shopee, TikTok Shop, website, WhatsApp",
            "Fulfillment butuh banyak material: kardus, pita, bubble wrap, kotak hampers, benang bordir",
            "Owner masih memilih dan mencatat vendor sendiri, memakai spreadsheet dan ingatan",
            "Sumber: dokumen Use Case UMKM Dicoding Bootcamp Batch 15 (Firaza)"], size=22)

# 3 why
s = slide("Termurah belum tentu terbaik", "b. Alasan memilih proyek")
card(s, 0.6, 1.8, 3.9, 3.6, "Harga", "Vendor murah bisa lambat atau berkualitas rendah.")
card(s, 4.7, 1.8, 3.9, 3.6, "Waktu", "Pesanan mendesak butuh vendor yang tepat waktu, bukan hanya cepat di atas kertas.")
card(s, 8.8, 1.8, 3.9, 3.6, "Skala", "Makin banyak vendor dan transaksi, makin sulit membandingkan secara konsisten dan mendelegasikan.")
text(s, 0.6, 5.7, 12, 1, "Painkiller: keputusan procurement yang konsisten, transparan, dan tidak bergantung pada satu orang.", 20, True, PURPLE)

# 4 similar solutions
s = slide("Apa yang sudah ada, dan apa yang kurang", "c. Analisis solusi serupa")
card(s, 0.6, 1.8, 5.9, 3.0, "Spreadsheet / rumus bobot",
     "Mudah, tapi linear: tidak menangkap aturan seperti 'pesanan mendesak harus menghindari vendor yang sering telat', dan tidak menjelaskan alasannya.")
card(s, 6.8, 1.8, 5.9, 3.0, "Modul supplier ERP / metode MCDM (TOPSIS)",
     "Lengkap tapi berat untuk UMKM; skor tanpa penjelasan bahasa natural dan tidak belajar dari histori.")
text(s, 0.6, 5.2, 12, 1.4, ["Celah: ranking yang belajar dari data dan menangkap trade-off non-linear,",
                            "plus penjelasan yang bisa dipercaya karena berbasis data (bukan karangan LLM)."], 20, True, TEAL)

# 5 solution & architecture
s = slide("Model memutuskan urutan, LLM menjelaskan", "d. Implementasi solusi")
card(s, 0.6, 1.8, 3.9, 4.2, "1 · Model ranking",
     "LightGBM LambdaRank dilatih sendiri. 17 fitur: harga relatif, lead time vs tenggat, ketepatan waktu, cacat, MOQ, stok, prioritas user.")
card(s, 4.7, 1.8, 3.9, 4.2, "2 · RAG",
     "Embedding Gemini + vector store ChromaDB. Ambil profil & kinerja vendor teratas + catatan kebijakan; Gemini menjelaskan. Angka dicek otomatis.", TEAL)
card(s, 8.8, 1.8, 3.9, 4.2, "3 · Aplikasi",
     "Streamlit (UI) + FastAPI (REST API & Swagger) + Postgres (Neon). API key hanya di server. Fallback template bila AI tidak tersedia.", GRAY)

# 6 data & preprocessing
s = slide("Data sintetis yang jujur + preprocessing nyata", "d. Implementasi solusi")
bullets(s, ["32 vendor · 12 material · 176 penawaran · 1.597 transaksi (seed tetap, bisa direproduksi)",
            "Masalah data disengaja: 15 duplikat, 7 waktu kirim mustahil, 31 nilai hilang, semuanya dibersihkan",
            "'Kebenaran tersembunyi' (keandalan & kualitas asli) hanya dipakai untuk label, tidak dilihat model",
            "3.000 permintaan simulasi → 44.253 baris; split per permintaan (70/15/15)"], w=6.4, size=18)
image(s, REPORTS / "eda_cleaning_before_after.png", 7.2, 1.9, w=5.8)

# 7 results ranking
s = slide("Model jauh di atas baseline", "e. Hasil akhir")
image(s, OUT / "chart_ndcg.png", 0.5, 1.6, w=7.2)
m = metrics["lightgbm_lambdarank"]
bullets(s, [f"NDCG@3 = {m['ndcg@3']:.3f} pada 450 permintaan uji (target ≥ 0,85)".replace(".", ",", 1),
            f"Baseline terbaik (rumus bobot): {metrics['baseline_weighted_sum']['ndcg@3']:.3f}".replace(".", ","),
            f"Kontrol label acak: {metrics['control_shuffled_labels']['ndcg@3']:.3f} → skor bukan kebetulan".replace(".", ","),
            "Fitur terpenting: harga relatif, prioritas harga, MOQ, sisa waktu ke tenggat"], x=8.0, y=1.9, w=4.9, size=16)

# 8 results RAG
s = slide("Penjelasan yang bisa ditelusuri", "e. Hasil akhir")
g, r = rag["generation"], rag["retrieval"]
card(s, 0.6, 1.8, 3.9, 2.4, "Retrieval Recall@3", f"{r['recall@3']:.1f} pada {r['n']} pertanyaan uji".replace(".", ","), TEAL)
card(s, 4.7, 1.8, 3.9, 2.4, "Faithfulness",
     f"{g['faithfulness']:.1f}: semua angka di {g['n_answered']} jawaban ada di konteks".replace(".", ",", 1), TEAL)
card(s, 8.8, 1.8, 3.9, 2.4, "Ketahanan",
     f"{g['n_requests'] - g['n_answered']} dari {g['n_requests']} permintaan kena overload Gemini → otomatis penjelasan template", GRAY)
text(s, 0.6, 4.6, 12, 2, ["Teks AI hanya boleh memakai angka dari konteks; jika gagal verifikasi, aplikasi memakai template.",
                          "Pengguna tidak pernah melihat angka karangan."], 18)

# 9 demo
s = slide("Demo aplikasi", "e. Hasil akhir")
ph = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.7), Inches(12.1), Inches(5.0))
ph.fill.solid(); ph.fill.fore_color.rgb = LIGHT; ph.line.color.rgb = PURPLE
text(s, 1.0, 3.6, 11.3, 1.2, "[Tempel screenshot halaman Rekomendasi Vendor di sini, lalu demo live saat presentasi]", 20,
     False, GRAY)

# 10 documentation & usage
s = slide("Dokumentasi & cara pakai", "f. Dokumentasi")
bullets(s, ["Repo open source (MIT): github.com/abidayn/Firaza",
            "README: instalasi, menjalankan app & API, retrain model, variabel lingkungan",
            "docs/: DATA_CARD, MODEL_CARD, ARCHITECTURE, USER_GUIDE (Bahasa Indonesia), SBOM & LICENSE_NOTES",
            "REST API + Swagger: /api/v1/recommendations, /explanation · 14 tes otomatis",
            "Keterbatasan: data sintetis (hasil = bukti pipeline, bukan akurasi data asli); tanpa login",
            "Langkah berikut: latih ulang dengan data & keputusan asli owner Firaza"], size=19)

prs.save(OUT / "firaza_pitch.pptx")
print("saved", OUT / "firaza_pitch.pptx", "slides:", len(prs.slides))
