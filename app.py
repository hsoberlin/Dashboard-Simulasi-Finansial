import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

# --- INITIALIZATION ---
if 'modal_awal' not in st.session_state: st.session_state.modal_awal = 1000000000
if 'tambahan_tahunan' not in st.session_state: st.session_state.tambahan_tahunan = 0
if 'dividen_tahun' not in st.session_state: st.session_state.dividen_tahun = 7.0

# Database internal Suku Bunga Perbankan
db_bank = {
    "Bank Himbara (BUMN)": {
        "KUR (Kredit Usaha Rakyat)": {"tipe": "fixed", "rate": 6.00},
        "Kredit Pegawai / Payroll Institusi": {"tipe": "fixed", "rate": 8.50},
        "KPR (Promo + Floating)": {"tipe": "floating", "promo": 6.00, "floating": 12.50}
    },
    "Bank Swasta Utama": {
        "KTA Umum (Non-Payroll)": {"tipe": "fixed", "rate": 14.50},
        "KPR (Promo + Floating)": {"tipe": "floating", "promo": 5.50, "floating": 12.00}
    }
}

tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Institusi", "Simulasi Investasi Bertahap", "Analisis Ekuitas Bersih"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN INSTITUSI
# ==========================================
with tab1:
    st.header(":orange[Kalkulator Pinjaman Berbasis Data Pasar]")
    col1, col2 = st.columns([1, 3])
    with col1:
        kategori_bank = st.selectbox("Pilih Institusi Perbankan", list(db_bank.keys()))
        jenis_kredit = st.selectbox("Jenis Fasilitas Kredit", list(db_bank[kategori_bank].keys()))
        data_kredit = db_bank[kategori_bank][jenis_kredit]
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=1000000000, step=50000000, format="%d")
        tenor_bulan = st.slider("Tenor Pinjaman (Bulan)", min_value=12, max_value=360, value=240, step=12)
        
        if data_kredit["tipe"] == "floating":
            bunga_promo = st.number_input("Suku Bunga Promo Awal (% p.a)", value=data_kredit["promo"], step=0.01)
            masa_promo_thn = st.number_input("Lama Masa Promo (Tahun)", value=3, step=1)
            bunga_floating = st.number_input("Suku Bunga Floating (% p.a)", value=data_kredit["floating"], step=0.01)
            masa_promo_bln = masa_promo_thn * 12
        else:
            bunga_tetap = st.number_input("Suku Bunga Efektif (% p.a)", value=data_kredit["rate"], step=0.01)
            
    with col2:
        saldo = plafon
        data_jadwal = []
        for bulan in range(1, tenor_bulan + 1):
            sisa_tenor = tenor_bulan - bulan + 1
            if data_kredit["tipe"] == "floating":
                bunga_bln = (bunga_promo if bulan <= masa_promo_bln else bunga_floating) / 100 / 12
                cicilan = (saldo * (bunga_bln * (1 + bunga_bln)**sisa_tenor) / ((1 + bunga_bln)**sisa_tenor - 1)) if bunga_bln > 0 else saldo/sisa_tenor
            else:
                bunga_bln = bunga_tetap / 100 / 12
                cicilan = (plafon * (bunga_bln * (1 + bunga_bln)**tenor_bulan) / ((1 + bunga_bln)**tenor_bulan - 1)) if bunga_bln > 0 else plafon/tenor_bulan
            porsi_bunga = saldo * bunga_bln
            porsi_pokok = cicilan - porsi_bunga
            saldo -= porsi_pokok
            data_jadwal.append([bulan, cicilan, porsi_pokok, porsi_bunga, max(0, saldo)])
        
        df_jadwal = pd.DataFrame(data_jadwal, columns=["Bulan", "Total Angsuran", "Porsi Pokok", "Porsi Bunga", "Sisa Pinjaman"])
