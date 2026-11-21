"""Transaction history (feeds on-time rate, delivery and defect stats used by the model)."""
import pandas as pd
import streamlit as st

from app_core import models, rp, services, session, setup, show_error

setup("Transaksi")
st.title("Histori Transaksi")
st.caption("Histori ini dipakai model untuk menghitung ketepatan waktu, lama pengiriman, dan tingkat cacat vendor.")

with session() as db:
    materials = services.list_rows(db, models.Material)
    vendors = services.list_rows(db, models.Vendor)
mnames = {m.id: m.name for m in materials}
vnames = {v.id: v.name for v in vendors}

c1, c2 = st.columns(2)
fv = c1.selectbox("Filter vendor", [None, *vnames], format_func=lambda i: "Semua vendor" if i is None else vnames[i])
fm = c2.selectbox("Filter material", [None, *mnames], format_func=lambda i: "Semua material" if i is None else mnames[i])
with session() as db:
    rows = services.list_rows(db, models.Transaction, vendor_id=fv, material_id=fm)
rows = sorted(rows, key=lambda t: t.ordered_at, reverse=True)
st.write(f"{len(rows)} transaksi")
st.dataframe(pd.DataFrame([{
    "ID": t.id, "Tanggal": t.ordered_at, "Vendor": vnames.get(t.vendor_id), "Material": mnames.get(t.material_id),
    "Jumlah": t.qty, "Harga satuan": rp(t.unit_price), "Dijanjikan (hari)": t.promised_days,
    "Aktual (hari)": t.actual_days, "Tepat waktu": "Ya" if t.actual_days <= t.promised_days else "Tidak",
    "Cacat": f"{t.defect_rate * 100:.1f}%" if t.defect_rate is not None else "-"} for t in rows[:500]]),
    hide_index=True, width="stretch")

st.subheader("Catat transaksi baru")
with st.form("add_tx", clear_on_submit=True):
    c1, c2 = st.columns(2)
    vendor_id = c1.selectbox("Vendor", list(vnames), format_func=vnames.get)
    material_id = c2.selectbox("Material", list(mnames), format_func=mnames.get)
    c1, c2, c3 = st.columns(3)
    qty = c1.number_input("Jumlah", min_value=1, value=100)
    price = c2.number_input("Harga satuan (Rp)", min_value=1.0, value=1000.0)
    ordered = c3.date_input("Tanggal pesan", value=services.today())
    c1, c2, c3 = st.columns(3)
    promised = c1.number_input("Dijanjikan (hari)", min_value=1, max_value=60, value=2)
    actual = c2.number_input("Aktual (hari)", min_value=0, max_value=365, value=2)
    defect = c3.number_input("Tingkat cacat (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
    if st.form_submit_button("Simpan transaksi", type="primary"):
        try:
            with session() as db:
                services.create_row(db, models.Transaction, {
                    "vendor_id": vendor_id, "material_id": material_id, "qty": int(qty), "unit_price": price,
                    "ordered_at": ordered, "promised_days": int(promised), "actual_days": int(actual),
                    "defect_rate": defect / 100})
            st.success("Transaksi dicatat")
            st.rerun()
        except Exception as exc:
            show_error(exc)
