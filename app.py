import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

# --- INITIALIZATION (Menyimpan state agar sinkron antar tab) ---
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
# TAB 1: KALKULATOR PINJAMAN
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
        st.dataframe(df_jadwal.head(10).style.format("{:,.0f}"))

# ==========================================
# TAB 2: SIMULASI INVESTASI BERTAHAP
# ==========================================
with tab2:
    st.header(":violet[Simulasi Investasi Bertahap]")
    col3, col4 = st.columns([1, 3])
    with col3:
        st.subheader("Parameter Investasi")
        # Menggunakan session_state agar nilai tersimpan permanen
        st.session_state.modal_awal = st.number_input("Modal Awal (Rp)", value=st.session_state.modal_awal, step=1000000)
        st.session_state.tambahan_tahunan = st.number_input("Suntikan Dana per Tahun (Rp)", value=st.session_state.tambahan_tahunan, step=10000000)
        st.session_state.dividen_tahun = st.number_input("Target Pertumbuhan (%)", value=st.session_state.dividen_tahun, step=0.1)
        lama_investasi = st.slider("Lama Investasi (Tahun)", 1, 50, 20)
        
    with col4:
        data_inv = []
        saldo = st.session_state.modal_awal
        total_setor = st.session_state.modal_awal
        for t in range(1, lama_investasi + 1):
            if t > 1: saldo += st.session_state.tambahan_tahunan; total_setor += st.session_state.tambahan_tahunan
            saldo *= (1 + st.session_state.dividen_tahun/100)
            data_inv.append([t, total_setor, saldo - total_setor, saldo])
        df_invest = pd.DataFrame(data_inv, columns=["Tahun", "Total Modal", "Profit", "Total Portofolio"])
        st.line_chart(df_invest.set_index("Tahun"))

# ==========================================
# TAB 3: ANALISIS PERSILANGAN (CROSSOVER)
# ==========================================
with tab3:
    st.header(":red[Analisis Persilangan: Hasil Dividen vs Beban Pinjaman]")
    st.write("Grafik ini menarik data dari input Tab 2 dan jadwal cicilan Tab 1 secara real-time.")
    
    # Mengambil nilai dari session_state agar sinkron 100%
    modal_awal = st.session_state.modal_awal
    tambahan_tahunan = st.session_state.tambahan_tahunan
    dividen_tahun = st.session_state.dividen_tahun
    cicilan_per_bulan = df_jadwal["Total Angsuran"].mean()
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    for thn in range(1, max_tahun + 1):
        if thn <= lama_investasi:
            nilai_investasi = modal_awal * (1 + (dividen_tahun / 100))**thn
        else:
            nilai_investasi = modal_awal * (1 + (dividen_tahun / 100))**lama_investasi
            
        akumulasi_dividen = nilai_investasi - modal_awal
        bulan_berjalan = min(thn * 12, tenor_bulan)
        akumulasi_cicilan = bulan_berjalan * cicilan_per_bulan
        
        data_cross.append([thn, akumulasi_dividen, akumulasi_cicilan])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Akumulasi Dividen", "Akumulasi Pembayaran"])
    
    fig_cross = go.Figure()
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Akumulasi Dividen"], name="Akumulasi Dividen (Profit)", line=dict(color='#00CC96', width=3)))
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Akumulasi Pembayaran"], name="Total Setoran ke Bank (Beban)", line=dict(color='#EF553B', width=3)))
    
    fig_cross.update_layout(title="Kurva Break-Even (Keuntungan vs Beban)", template="plotly_dark")
    st.plotly_chart(fig_cross, use_container_width=True)
