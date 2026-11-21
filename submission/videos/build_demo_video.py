"""Build the captioned demo video (submission/videos/demo_fitur_ai.mp4) from live-app screenshots.

Frames are screenshots of https://firaza-vendor.streamlit.app saved in submission/videos/frames/.
Needs Pillow and ffmpeg (pip install imageio-ffmpeg).
Run from the repo root:  .venv/Scripts/python submission/videos/build_demo_video.py
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

if os.getenv("PYLIB"):
    sys.path.insert(0, os.environ["PYLIB"])
import imageio_ffmpeg  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"
OUT = HERE / "demo_fitur_ai.mp4"
W, H, BAND = 1280, 800, 150
PURPLE, WHITE, DARK = (83, 74, 183), (255, 255, 255), (20, 20, 22)

SCENES = [  # (frame file or None for a title card, seconds, caption)
    (None, 6, "Firaza · Asisten Rekomendasi Vendor||Demo fitur AI · Capstone Dicoding Bootcamp Batch 15 · DB15-I036 · Abid Dayyan"),
    ("01_beranda.png", 10, "Aplikasi live di firaza-vendor.streamlit.app. Status: model ranking siap, penjelasan AI memakai Gemini, "
                           "vector store ChromaDB, dan data tersimpan di database Postgres (Neon): 32 vendor, 1.597 transaksi."),
    ("02_hasil.png", 13, "Kebutuhan: 100 kardus 30x20x15 cm, tenggat 3 hari, prioritas kecepatan 50%. Model ranking LightGBM yang "
                         "dilatih sendiri mengurutkan 17 vendor. Rekomendasi utama: PT Prima Sinar (lead time 1 hari)."),
    ("03_catatan.png", 9, "Tabel menandai risiko setiap vendor secara otomatis, misalnya stok kosong, melewati tenggat, "
                          "atau pesanan di bawah MOQ."),
    ("04_penjelasan.png", 14, "Grafik kiri: total harga. Grafik kanan: faktor yang paling menaikkan skor vendor teratas, langsung dari "
                              "model. Di bawahnya, RAG + Gemini menjelaskan alasan, trade-off (lebih mahal Rp 8.000 tapi lebih cepat), "
                              "dan risikonya."),
    ("05_sumber.png", 11, "Penjelasan disusun hanya dari dokumen yang diambil dari vector store: profil dan kinerja 3 vendor teratas "
                          "serta catatan kebijakan yang relevan. Setiap angka dicek otomatis terhadap data."),
    ("06_material.png", 9, "Data penawaran vendor (harga, harga grosir, MOQ, lead time, stok, kualitas) dapat ditambah dan diubah "
                           "langsung di aplikasi."),
    ("07_transaksi.png", 9, "Histori transaksi dipakai model untuk menghitung ketepatan waktu, lama pengiriman, dan tingkat cacat "
                            "tiap vendor."),
    ("08_vendor.png", 7, "Manajemen vendor: tambah, ubah, dan hapus (dengan pengecekan data yang masih dipakai)."),
    ("09_swagger.png", 10, "Hasil yang sama tersedia lewat REST API (FastAPI + Swagger): POST /api/v1/recommendations "
                           "mengembalikan ranking dalam format JSON."),
    (None, 6, "Terima kasih||Kode open source (MIT): github.com/abidayn/Firaza · Aplikasi: firaza-vendor.streamlit.app"),
]


def font(size, bold=False):
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def title_card(text):
    img = Image.new("RGB", (W, H), PURPLE)
    d = ImageDraw.Draw(img)
    title, sub = text.split("||")
    d.text((W // 2, H // 2 - 40), title, font=font(52, True), fill=WHITE, anchor="mm")
    for i, line in enumerate(textwrap.wrap(sub, 80)):
        d.text((W // 2, H // 2 + 40 + i * 36), line, font=font(24), fill=(238, 237, 254), anchor="mm")
    return img


def captioned(frame, caption):
    shot = Image.open(FRAMES / frame).convert("RGB")
    img = Image.new("RGB", (W, H), DARK)
    area_h = H - BAND
    shot.thumbnail((W, area_h), Image.LANCZOS) if shot.width > W else None
    scale = min(W / shot.width, area_h / shot.height)
    shot = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
    img.paste(shot, ((W - shot.width) // 2, (area_h - shot.height) // 2))
    d = ImageDraw.Draw(img)
    d.rectangle([0, area_h, W, H], fill=PURPLE)
    for i, line in enumerate(textwrap.wrap(caption, 95)[:4]):
        d.text((40, area_h + 22 + i * 30), line, font=font(24), fill=WHITE)
    return img


def main():
    tmp = HERE / "_render"
    tmp.mkdir(exist_ok=True)
    lst = []
    for i, (frame, secs, caption) in enumerate(SCENES):
        img = title_card(caption) if frame is None else captioned(frame, caption)
        path = tmp / f"s{i:02d}.png"
        img.save(path)
        lst.append(f"file '{path.as_posix()}'\nduration {secs}")
    lst.append(f"file '{(tmp / f's{len(SCENES) - 1:02d}.png').as_posix()}'")
    (tmp / "list.txt").write_text("\n".join(lst), encoding="utf-8")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"),
                    "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-movflags", "+faststart", str(OUT)], check=True)
    total = sum(s for _, s, _ in SCENES)
    print(f"saved {OUT} ({total} s, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
