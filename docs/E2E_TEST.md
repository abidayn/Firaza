# End-to-end test on production (2026-11-21)

Run against the **production Neon Postgres database** with the same code the live app runs (`https://firaza-vendor.streamlit.app`), including real Gemini calls. Raw results: `ml/reports/e2e_prod.json`.

Checks per scenario: at least 5 candidates, results sorted by model score, `misses_deadline` flag correct for every vendor, explanation returned.

| # | Scenario | Material | Qty | Deadline (days) | Candidates | Rank 1 | Rank-1 lead time | Explanation source | Time (s) | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Kardus kecil, standar | Kardus 30x20x15 cm | 100 | 3 | 17 | PT Prima Sinar | 1 | llm | 5.0 | ✅ |
| 2 | Kardus besar, partai besar, prioritas harga | Kardus 40x30x20 cm | 500 | 7 | 12 | UD Utama Mulia | 1 | llm | 2.5 | ✅ |
| 3 | Pita satin, mendesak 1 hari | Pita satin 2 cm | 50 | 1 | 18 | UD Indah Mulia | 1 | llm | 2.4 | ✅ |
| 4 | Pita grosgrain, kualitas utama | Pita grosgrain | 100 | 5 | 5 | Toko Berkah Sentosa | 2 | llm | 3.0 | ✅ |
| 5 | Bubble wrap, seimbang | Plastik bubble wrap | 200 | 3 | 14 | UD Utama Mulia | 2 | llm | 4.2 | ✅ |
| 6 | Polymailer, jumlah kecil (uji MOQ) | Polymailer 25x35 cm | 20 | 5 | 18 | Toko Utama Indah | 3 | llm | 13.1 | ✅ |
| 7 | Kotak hampers premium, mendesak | Kotak hampers premium | 50 | 2 | 17 | PT Mulia Prima | 4 (late) | llm | 2.9 | ✅ |
| 8 | Benang bordir, kualitas | Benang bordir | 100 | 10 | 19 | UD Utama Mulia | 1 | llm | 2.9 | ✅ |
| 9 | Label stiker, hanya harga | Label stiker custom | 500 | 7 | 12 | PT Prima Sinar | 3 | llm | 4.2 | ✅ |
| 10 | Lakban, hanya kecepatan | Lakban bening 2 inch | 100 | 1 | 11 | UD Abadi Sinar | 1 | llm | 2.8 | ✅ |

Notes:
- Scenario 6: the first Gemini model returned `504 DEADLINE_EXCEEDED`; the app moved to the next model in the chain and still produced an LLM explanation.
- Scenario 7: no vendor can deliver premium hamper boxes within 2 days (fastest lead time is 3 days). Every vendor is flagged *melewati tenggat* and the explanation points out the risk, rather than hiding it.

## Error paths

| Case | Result | Pass |
|---|---|---|
| material tidak ada (id 999) | NotFound: Material id 999 tidak ditemukan | ✅ |
| semua bobot 0 | Invalid: Minimal satu prioritas (harga, kecepatan, kualitas) harus lebih dari 0 | ✅ |
| hapus vendor yang masih punya penawaran | Conflict: Tidak bisa dihapus: masih dipakai oleh 6 baris di vendor_materials | ✅ |

## Live UI checks (browser, https://firaza-vendor.streamlit.app)

| Check | Result |
|---|---|
| Home page status | Model ranking *Siap*, *Gemini aktif*, vector store *chromadb*, 32 vendors, data from Neon |
| Recommendation page (kardus 30x20x15, 100 pcs, 3 days) | ranking, flags, both charts render; explanation shown |
| Gemini overloaded (504 on all models) | template explanation shown with label *Penjelasan template (Gemini tidak tersedia)*; no crash |
| Material & Harga, Vendor, Transaksi pages | load and list data from Neon |
