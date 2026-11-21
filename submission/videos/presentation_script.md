# Naskah video presentasi (10 menit, Bahasa Indonesia, kamera menyala)

Total target: 10:00. Bicara santai, jangan dibaca kata per kata. Angka dalam [kurung] diambil dari laporan di repo.

| Waktu | Slide | Yang diucapkan |
|---|---|---|
| 0:00–0:45 | 1. Judul | "Halo, saya Abid Dayyan, peserta Dicoding Bootcamp Batch 15 learning path Generative AI, ID grup DB15-I036. Saya mengerjakan capstone secara individu untuk UMKM Firaza, use case Vendor Recommendation and Procurement Assistant." |
| 0:45–1:45 | 2. Latar belakang | "Firaza menjual hampers dan personalized gifts, seperti handuk dan sajadah custom. Sekitar 99% penjualannya online. Untuk mengemas pesanan, Firaza membeli banyak material dari banyak vendor: kardus, pita, packaging, benang bordir. Saat ini pemilihan vendor dilakukan langsung oleh owner, berdasarkan spreadsheet dan ingatan." |
| 1:45–2:45 | 3. Masalah | "Masalahnya, harga bukan satu-satunya faktor. Vendor termurah bisa lambat, kualitasnya rendah, atau sering telat. Ketika jumlah vendor dan transaksi bertambah, membandingkan semua faktor secara konsisten jadi sulit, dan proses ini tidak bisa didelegasikan karena bergantung pada owner. Ini masalah nyata, painkiller, bukan vitamin." |
| 2:45–3:30 | 4. Solusi serupa | "Solusi yang ada biasanya spreadsheet dengan rumus bobot, atau fitur supplier di sistem ERP. Rumus bobot itu linear dan tidak menangkap aturan seperti 'kalau mendesak, vendor yang sering telat harus dihindari'. Dan keduanya tidak menjelaskan alasan rekomendasi dalam bahasa yang mudah dipahami." |
| 3:30–4:30 | 5. Solusi & arsitektur | "Solusi saya punya dua bagian AI. Pertama, model ranking yang saya latih sendiri, LightGBM LambdaRank, untuk mengurutkan vendor. Kedua, RAG untuk menjelaskan alasannya. Aplikasinya Streamlit, dengan REST API FastAPI, database Postgres di Neon, dan semua kunci API disimpan di server. Model yang memutuskan urutan; LLM hanya menjelaskan." |
| 4:30–5:30 | 6. Data & preprocessing | "Firaza tidak menyediakan data, jadi saya membuat data sintetis yang realistis: 32 vendor, 12 material, sekitar 1.600 transaksi. Saya sengaja memasukkan masalah data: duplikat, data hilang, dan waktu kirim yang mustahil, lalu membersihkannya di tahap preprocessing. Tiap vendor punya 'kebenaran tersembunyi' tentang keandalan dan kualitasnya, yang tidak dilihat model." |
| 5:30–6:45 | 7. Model ranking & hasil | "Model dilatih dengan 3.000 permintaan simulasi, dibagi per permintaan supaya tidak bocor. Metriknya NDCG@3, yaitu apakah vendor terbaik masuk 3 teratas. Model saya mencapai [0,933], di atas target 0,85, dan jauh di atas baseline: termurah [0,733], rumus bobot [0,788], dan TOPSIS [0,718]. Sebagai kontrol, model yang dilatih dengan label diacak hanya [0,456], jadi hasilnya bukan kebetulan." |
| 6:45–7:45 | 8. RAG | "Untuk penjelasan, sistem mengambil profil dan kinerja tiga vendor teratas, plus catatan kebijakan yang paling relevan, menggunakan embedding Gemini dan vector store ChromaDB. Gemini lalu menulis penjelasan hanya dari konteks itu. Setiap angka di teks dicek otomatis; kalau ada angka yang tidak ada di konteks, sistem memakai penjelasan template. Hasil evaluasi: Recall@3 retrieval [1,0], dan faithfulness [1,0]." |
| 7:45–9:15 | 9. Demo | (Bagikan layar aplikasi live.) "Saya pilih kardus 30x20x15, 100 pcs, tenggat 3 hari, prioritas kecepatan. Ini urutan vendornya, grafik total harga, dan faktor yang paling memengaruhi skor. Di bawah ini penjelasan AI, dan di sini dokumen yang dipakai. Data vendor, harga, dan transaksi juga bisa dikelola dari menu di samping." |
| 9:15–10:00 | 10. Keterbatasan & penutup | "Keterbatasannya: data masih sintetis, jadi angka di atas membuktikan pipeline-nya bekerja, bukan akurasi di data asli Firaza. Langkah berikutnya adalah memakai data dan keputusan asli owner untuk melatih ulang model. Kode dan dokumentasinya open source dengan lisensi MIT di GitHub. Terima kasih." |

## Tips rekaman
- Zoom atau Google Meet: nyalakan kamera, share screen ke slide, klik Record. Wajah harus terlihat sepanjang video.
- Buka aplikasi live sebelum mulai supaya tidak menunggu server bangun saat demo.
- Latih sekali dengan timer; potong kalimat jika lewat dari 10 menit.
