"""Vendor CRUD."""
import pandas as pd
import streamlit as st

from app_core import models, services, session, setup, show_error

setup("Vendor")
st.title("Vendor")

with session() as db:
    vendors = services.list_rows(db, models.Vendor)
st.dataframe(pd.DataFrame([{"ID": v.id, "Nama": v.name, "Kota": v.city, "Catatan": v.notes} for v in vendors]),
             hide_index=True, width="stretch")

add, edit = st.tabs(["Tambah vendor", "Ubah / hapus"])

with add:
    with st.form("add_vendor", clear_on_submit=True):
        name = st.text_input("Nama vendor", placeholder="CV Kemasan Baru")
        city = st.text_input("Kota", placeholder="Bandung")
        notes = st.text_area("Catatan", placeholder="Kontak, syarat pembayaran, dll.")
        if st.form_submit_button("Simpan", type="primary"):
            try:
                with session() as db:
                    services.create_row(db, models.Vendor, {"name": name.strip(), "city": city.strip(), "notes": notes})
                st.success("Vendor ditambahkan")
                st.rerun()
            except Exception as exc:
                show_error(exc)

with edit:
    if vendors:
        by_id = {v.id: v for v in vendors}
        vid = st.selectbox("Pilih vendor", list(by_id), format_func=lambda i: f"{i} · {by_id[i].name}")
        v = by_id[vid]
        with st.form(f"edit_vendor_{vid}"):
            name = st.text_input("Nama vendor", v.name)
            city = st.text_input("Kota", v.city)
            notes = st.text_area("Catatan", v.notes)
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("Simpan perubahan", type="primary")
            delete = c2.form_submit_button("Hapus vendor")
        try:
            if save:
                with session() as db:
                    services.update_row(db, models.Vendor, vid, {"name": name.strip(), "city": city.strip(), "notes": notes})
                st.success("Perubahan disimpan")
                st.rerun()
            if delete:
                with session() as db:
                    services.delete_row(db, models.Vendor, vid)
                st.success("Vendor dihapus")
                st.rerun()
        except Exception as exc:
            show_error(exc)
