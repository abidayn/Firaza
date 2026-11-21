# Naskah video demo fitur AI (sekitar 3 menit)

Rekam layar aplikasi **live** (URL Streamlit), narasi Bahasa Indonesia. Kamera boleh mati.

| Waktu | Tampilan | Narasi |
|---|---|---|
| 0:00–0:20 | Halaman **Beranda** | "Ini aplikasi Asisten Rekomendasi Vendor untuk Firaza. Di sini terlihat model ranking sudah siap, penjelasan AI memakai Gemini, dan datanya 32 vendor dengan sekitar 1.600 transaksi." |
| 0:20–0:50 | **Rekomendasi Vendor**, isi form | "Saya butuh 100 kardus 30x20x15 dalam 3 hari. Prioritas utama saya kecepatan, lalu harga, lalu kualitas. Klik Cari rekomendasi." |
| 0:50–1:30 | Tabel + grafik | "Model ranking LightGBM yang saya latih mengurutkan semua vendor. Kotak hijau adalah rekomendasi utama. Tabel menunjukkan skor, harga, lead time, kualitas, dan ketepatan waktu; vendor yang melewati tenggat diberi catatan. Grafik kanan menunjukkan faktor yang paling menaikkan skor vendor teratas, langsung dari model." |
| 1:30–2:15 | **Penjelasan AI** + expander dokumen | "Di bawahnya, RAG menjelaskan alasannya: Gemini menulis dari dokumen profil, kinerja vendor, dan catatan kebijakan yang diambil dari vector store. Ini daftar dokumen yang dipakai. Setiap angka di penjelasan dicek otomatis terhadap data." |
| 2:15–2:40 | Ubah input: tenggat 1 hari, kotak hampers premium | "Kalau pesanannya mendesak, urutannya berubah: vendor yang lambat atau sering telat turun, dan penjelasannya merujuk kebijakan pesanan mendesak." |
| 2:40–3:00 | Halaman **Material & Harga** / **Transaksi** | "Data vendor, harga, dan transaksi bisa dikelola langsung di aplikasi dan tersimpan di database, sehingga rekomendasi selalu memakai data terbaru." |

Opsional (jika REST API juga di-deploy, atau dari laptop): tampilkan `http://localhost:8000/docs` dan jalankan `POST /api/v1/recommendations` selama 10 detik untuk menunjukkan inference API.
