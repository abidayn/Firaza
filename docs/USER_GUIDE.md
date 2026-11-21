# Panduan Pengguna — Asisten Rekomendasi Vendor Firaza

Aplikasi ini membantu owner dan karyawan Firaza memilih vendor material (kardus, pita, packaging, bahan bordir/printing) secara konsisten. Aplikasi hanya memberi **saran**; keputusan akhir tetap di tangan pengguna.

## Halaman
| Halaman | Kegunaan |
|---|---|
| **Beranda** | Status sistem (model, penjelasan AI, vector store), jumlah data, permintaan terakhir |
| **Rekomendasi Vendor** | Halaman utama: masukkan kebutuhan, dapatkan urutan vendor dan penjelasannya |
| **Vendor** | Tambah, ubah, hapus data vendor |
| **Material & Harga** | Lihat dan kelola penawaran tiap vendor per material: harga, harga grosir, MOQ, lead time, stok, skor kualitas |
| **Transaksi** | Lihat histori pembelian dan catat transaksi baru (dipakai model untuk menilai ketepatan waktu dan tingkat cacat) |

## Alur utama: mencari rekomendasi
1. Buka **Rekomendasi Vendor**.
2. Pilih **Material**, isi **Jumlah** dan **Tenggat (hari)**.
3. Geser tiga slider **prioritas**: *Harga murah*, *Cepat & tepat waktu*, *Kualitas*. Nilainya dinormalisasi otomatis, jadi yang penting perbandingannya.
4. Klik **Cari rekomendasi**.
5. Baca hasilnya:
   - **Kotak hijau**: vendor rekomendasi utama.
   - **Tabel**: semua vendor berurutan, dengan skor 0–100, harga, lead time, kualitas, ketepatan waktu, dan catatan (melewati tenggat, di bawah MOQ, stok kosong).
   - **Grafik kiri**: total harga 8 vendor teratas.
   - **Grafik kanan**: faktor yang paling menaikkan atau menurunkan skor vendor utama, langsung dari model.
   - **Penjelasan AI**: alasan rekomendasi, trade-off dengan alternatif, dan satu risiko. Label di bawahnya menunjukkan apakah teks dibuat Gemini dari dokumen RAG atau berupa template (saat Gemini tidak tersedia). Buka **Dokumen yang dipakai** untuk melihat dokumen sumber.

## Contoh
Butuh 100 kardus 30x20x15 cm dalam 3 hari, prioritas kecepatan 50%, harga 30%, kualitas 20%. Aplikasi menempatkan vendor yang bisa kirim 1–2 hari dengan harga bersaing di atas, dan menjelaskan, misalnya, bahwa vendor teratas sedikit lebih mahal dari yang termurah namun lebih cepat, beserta catatan risiko ketepatan waktunya.

## Mengelola data
- **Vendor**: tab *Tambah vendor* atau *Ubah / hapus*. Vendor yang masih punya penawaran atau transaksi tidak bisa dihapus (hapus penawarannya dulu).
- **Material & Harga**: pilih material, lalu tambah atau ubah penawaran vendor. Harga grosir berlaku mulai jumlah *Grosir mulai*.
- **Transaksi**: catat setiap pembelian beserta hari yang dijanjikan dan hari aktual. Semakin banyak histori, semakin akurat penilaian ketepatan waktu vendor.

## Catatan
- Data di prototipe ini **sintetis** (bukan data asli Firaza).
- Jika server baru bangun dari mode tidur (hosting gratis), pemuatan pertama bisa memakan waktu sekitar satu menit.
