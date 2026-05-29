import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

# --- SINKRONISASI VARIABEL ANTAR TAB (SESSION STATE) ---
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

tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Institusi", "Simulasi Investasi Bertahap", "Analisis Margin & Pelunasan"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN INSTITUSI
# ==========================================
with tab1:
    st.header(":orange[Kalkulator Pinjaman Berbasis Data Pasar]")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Parameter Institusi")
        kategori_bank = st.selectbox("Pilih Institusi Perbankan", list(db_bank.keys()))
        jenis_kredit = st.selectbox("Jenis Fasilitas Kredit", list(db_bank[kategori_bank].keys()))
        data_kredit = db_bank[kategori_bank][jenis_kredit]
        
        st.markdown("---")
        st.subheader("Parameter Pinjaman")
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
        
        # --- PERBAIKAN LOGIKA: Hitung cicilan agar tetap (Fixed) per fase ---
        if data_kredit["tipe"] == "floating":
            b_promo = (bunga_promo / 100) / 12
            cicilan_promo = (plafon * (b_promo * (1 + b_promo)**tenor_bulan) / ((1 + b_promo)**tenor_bulan - 1)) if b_promo > 0 else plafon/tenor_bulan
            
            saldo_temp = plafon
            for b in range(1, masa_promo_bln + 1):
                porsi_bunga_t = saldo_temp * b_promo
                saldo_temp -= (cicilan_promo - porsi_bunga_t)
            
            b_float = (bunga_floating / 100) / 12
            sisa_tenor_float = tenor_bulan - masa_promo_bln
            cicilan_floating = (saldo_temp * (b_float * (1 + b_float)**sisa_tenor_float) / ((1 + b_float)**sisa_tenor_float - 1)) if b_float > 0 else saldo_temp/sisa_tenor_float
        else:
            b_tetap = bunga_tetap / 100 / 12
            cicilan_tetap = (plafon * (b_tetap * (1 + b_tetap)**tenor_bulan) / ((1 + b_tetap)**tenor_bulan - 1)) if b_tetap > 0 else plafon/tenor_bulan

        # --- LOOP GENERATE JADWAL ---
        saldo = plafon
        for bulan in range(1, tenor_bulan + 1):
            if data_kredit["tipe"] == "floating":
                bunga_bln = (bunga_promo if bulan <= masa_promo_bln else bunga_floating) / 100 / 12
                cicilan = cicilan_promo if bulan <= masa_promo_bln else cicilan_floating
            else:
                bunga_bln = bunga_tetap / 100 / 12
                cicilan = cicilan_tetap
                
            porsi_bunga = saldo * bunga_bln
            porsi_pokok = cicilan - porsi_bunga
            saldo = max(0, saldo - porsi_pokok)
            data_jadwal.append([bulan, cicilan, porsi_pokok, porsi_bunga, saldo])
        
        df_jadwal = pd.DataFrame(data_jadwal, columns=["Bulan", "Total Angsuran", "Porsi Pokok", "Porsi Bunga", "Sisa Pinjaman"])

# ==========================================
# TAB 2: SIMULASI INVESTASI BERTAHAP
# ==========================================
with tab2:
    st.header(":violet[Simulasi Investasi Bertahap]")
    col3, col4 = st.columns([1, 3])
    with col3:
        st.session_state.modal_awal = st.number_input("Modal Awal (Rp)", value=st.session_state.modal_awal, step=10000000)
        st.session_state.tambahan_tahunan = st.number_input("Suntikan Dana per Tahun (Mulai Thn ke-2)", value=st.session_state.tambahan_tahunan, step=5000000)
        st.session_state.dividen_tahun = st.number_input("Target Pertumbuhan Tahunan (%)", value=st.session_state.dividen_tahun, step=0.1)
        lama_investasi = st.slider("Lama Investasi (Tahun)", 1, 50, 20)
        
    with col4:
        data_inv = []
        saldo_running = st.session_state.modal_awal
        total_modal_disetor = st.session_state.modal_awal
        
        for t in range(1, lama_investasi + 1):
            if t > 1: 
                saldo_running += st.session_state.tambahan_tahunan
                total_modal_disetor += st.session_state.tambahan_tahunan
            saldo_running *= (1 + st.session_state.dividen_tahun/100)
            profit_murni = saldo_running - total_modal_disetor
            data_inv.append([t, total_modal_disetor, profit_murni, saldo_running])
            
        df_invest = pd.DataFrame(data_inv, columns=["Tahun", "Total Modal Disetor", "Akumulasi Profit", "Total Portofolio"])
        st.subheader(f"Total Nilai Portofolio Akhir: :green[Rp {saldo_running:,.0f}]")
        
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Total Modal Disetor"], mode='lines', stackgroup='one', name="Total Modal Disetor", fillcolor='#19D3F3', line=dict(width=0))) 
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Profit"], mode='lines', stackgroup='one', name="Akumulasi Profit", fillcolor='#AB63FA', line=dict(width=0))) 
        fig_invest.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
        st.plotly_chart(fig_invest, use_container_width=True)

# ==========================================
# TAB 3: ANALISIS PENGAJUAN INVESTOR (VERSION 4.2 - DINAMIS)
# ==========================================
with tab3:
    st.header(":red[Executive Summary: Profil Risiko & Pertumbuhan]")
    
    # 1. Kalkulasi Data
    max_tahun = max(math.ceil(tenor_bulan / 12), lama_investasi)
    data_cross = []
    saldo_akhir = st.session_state.modal_awal
    modal_total_disetor = st.session_state.modal_awal
    
    for thn in range(1, max_tahun + 1):
        # Aset
        if thn > 1 and thn <= lama_investasi:
            saldo_akhir += st.session_state.tambahan_tahunan
            modal_total_disetor += st.session_state.tambahan_tahunan
        saldo_akhir *= (1 + st.session_state.dividen_tahun/100)
        
        # Sunk Cost (Akumulasi Cicilan)
        bulan_akhir = min(thn * 12, tenor_bulan)
        uang_cicilan = df_jadwal.iloc[:bulan_akhir]["Total Angsuran"].sum()
        sisa_hutang = df_jadwal.iloc[bulan_akhir - 1]["Sisa Pinjaman"] if bulan_akhir < tenor_bulan else 0
        
        total_uang_terbakar = modal_total_disetor + uang_cicilan
        akumulasi_margin = saldo_akhir - modal_total_disetor
        
        data_cross.append([thn, saldo_akhir, total_uang_terbakar, akumulasi_margin, sisa_hutang])

    df = pd.DataFrame(data_cross, columns=["Tahun", "Total Aset", "Total Uang Terbakar", "Margin Keuntungan", "Sisa Hutang"])
    
    # 2. Grafik Utama
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Total Aset"], name="Total Nilai Aset", line=dict(color='#00CC96', width=4)))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Total Uang Terbakar"], name="Total Uang Terbakar", line=dict(color='#FFA15A', width=3, dash='dot')))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Margin Keuntungan"], name="Akumulasi Margin", line=dict(color='#636EFA', width=3)))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Sisa Hutang"], name="Sisa Pokok Hutang", line=dict(color='#EF553B', width=3)))
    
    fig.update_layout(template="plotly_dark", height=500, hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Analisis Dinamis
    df['Selisih_Aset_Terbakar'] = df['Total Aset'] - df['Total Uang Terbakar']
    df['Selisih_Margin_Hutang'] = df['Margin Keuntungan'] - df['Sisa Hutang']
    
    be_aset = df[df['Selisih_Aset_Terbakar'] > 0]
    thn_be_aset = be_aset.iloc[0]['Tahun'] if not be_aset.empty else "di luar periode simulasi"
    
    be_margin = df[df['Selisih_Margin_Hutang'] > 0]
    thn_be_margin = be_margin.iloc[0]['Tahun'] if not be_margin.empty else "di luar periode simulasi"

    st.subheader("Data-Driven Executive Summary")
    st.markdown(f"""
    * **Capital Protection:** Nilai portofolio diproyeksikan melampaui total kumulatif dana yang dibakar (Cicilan + Modal) pada **Tahun ke-{thn_be_aset}**. Ini adalah *buffer* nilai yang menjadi jaminan keamanan modal.
    * **Risk-Free Exit Strategy:** Proyek ini memiliki kapasitas melunasi seluruh sisa pokok hutang secara mandiri menggunakan akumulasi margin pada **Tahun ke-{thn_be_margin}**. Pada titik ini, modal utama Anda tetap utuh 100%.
    * **Financial Resilience:** Rasio pertumbuhan aset menunjukkan efisiensi *leverage* yang konsisten, di mana laju *compounding* aset secara sistematis menekan biaya bunga.
    """)
