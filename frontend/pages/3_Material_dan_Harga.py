"""Materials and vendor offers (price, lead time, quality, MOQ, stock)."""
import pandas as pd
import streamlit as st

from app_core import models, rp, services, session, setup, show_error

setup("Material & Harga")
st.title("Material & Harga")

with session() as db:
    materials = services.list_rows(db, models.Material)
    vendors = services.list_rows(db, models.Vendor)
mats = {m.id: m for m in materials}
vnames = {v.id: v.name for v in vendors}

mid = st.selectbox("Material", list(mats), format_func=lambda i: f"{mats[i].name} ({mats[i].unit})")
with session() as db:
    offers = services.list_rows(db, models.VendorMaterial, material_id=mid)
st.dataframe(pd.DataFrame([{
    "ID": o.id, "Vendor": vnames.get(o.vendor_id, o.vendor_id), "Harga satuan": rp(o.unit_price),
    "Harga grosir": rp(o.bulk_unit_price) if o.bulk_unit_price else "-", "Grosir mulai": o.bulk_min_qty or "-",
    "MOQ": o.moq, "Lead time (hari)": o.lead_time_days, "Stok": "Ada" if o.in_stock else "Kosong",
    "Kualitas": o.quality_score} for o in offers]), hide_index=True, width="stretch")


def offer_form(key: str, o=None):
    with st.form(key):
        c1, c2 = st.columns(2)
        vendor_id = c1.selectbox("Vendor", list(vnames), format_func=vnames.get,
                                 index=list(vnames).index(o.vendor_id) if o else 0, disabled=o is not None)
        unit_price = c2.number_input("Harga satuan (Rp)", min_value=1.0, value=float(o.unit_price) if o else 1000.0)
        c1, c2, c3 = st.columns(3)
        bulk_min = c1.number_input("Grosir mulai (qty)", min_value=1, value=int(o.bulk_min_qty or 100) if o else 100)
        bulk_price = c2.number_input("Harga grosir (Rp)", min_value=1.0,
                                     value=float(o.bulk_unit_price or o.unit_price) if o else 900.0)
        moq = c3.number_input("MOQ", min_value=1, value=int(o.moq) if o else 10)
        c1, c2, c3 = st.columns(3)
        lead = c1.number_input("Lead time (hari)", min_value=1, max_value=60, value=int(o.lead_time_days) if o else 2)
        quality = c2.slider("Skor kualitas", 1.0, 5.0, float(o.quality_score) if o else 4.0, 0.1)
        in_stock = c3.checkbox("Stok tersedia", value=bool(o.in_stock) if o else True)
        buttons = st.columns(2)
        save = buttons[0].form_submit_button("Simpan", type="primary")
        delete = buttons[1].form_submit_button("Hapus penawaran") if o else False
    data = {"vendor_id": vendor_id, "material_id": mid, "unit_price": unit_price, "bulk_min_qty": int(bulk_min),
            "bulk_unit_price": bulk_price, "moq": int(moq), "lead_time_days": int(lead), "in_stock": in_stock,
            "quality_score": round(quality, 1)}
    return save, delete, data


add, edit = st.tabs(["Tambah penawaran", "Ubah / hapus penawaran"])
with add:
    save, _, data = offer_form("add_offer")
    if save:
        try:
            with session() as db:
                services.create_row(db, models.VendorMaterial, data)
            st.success("Penawaran ditambahkan")
            st.rerun()
        except Exception as exc:
            show_error(exc)
with edit:
    if offers:
        by_id = {o.id: o for o in offers}
        oid = st.selectbox("Pilih penawaran", list(by_id), format_func=lambda i: vnames.get(by_id[i].vendor_id, i))
        save, delete, data = offer_form(f"edit_offer_{oid}", by_id[oid])
        try:
            if save:
                with session() as db:
                    services.update_row(db, models.VendorMaterial, oid, data)
                st.success("Perubahan disimpan")
                st.rerun()
            if delete:
                with session() as db:
                    services.delete_row(db, models.VendorMaterial, oid)
                st.success("Penawaran dihapus")
                st.rerun()
        except Exception as exc:
            show_error(exc)
