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

tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Institusi", "Simulasi Investasi Bertahap", "Analisis Pengajuan Dana"])

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
        
        # Ringkasan Total Pembayaran
        total_pembayaran_kredit = df_jadwal["Total Angsuran"].sum()
        total_beban_bunga = df_jadwal["Porsi Bunga"].sum()
        
        st.subheader(f"Total Kewajiban Pinjaman Hingga Lunas: :red[Rp {total_pembayaran_kredit:,.0f}]")
        
        cm1, cm2 = st.columns(2)
        cm1.metric("Total Pokok Hutang", f"Rp {plafon:,.0f}")
        cm2.metric("Total Biaya Bunga (Cost of Credit)", f"Rp {total_beban_bunga:,.0f}")
        
        # PERBAIKAN VISUAL: Hilangkan garis tepi (marker_line_width=0) dan gap (bargap=0)
        fig_pinjaman = go.Figure()
        fig_pinjaman.add_trace(go.Bar(
            x=df_jadwal["Bulan"], y=df_jadwal["Porsi Pokok"], 
            name="Porsi Pokok", marker_color='#00CC96', marker_line_width=0
        ))
        fig_pinjaman.add_trace(go.Bar(
            x=df_jadwal["Bulan"], y=df_jadwal["Porsi Bunga"], 
            name="Porsi Bunga", marker_color='#EF553B', marker_line_width=0
        ))
        fig_pinjaman.update_layout(
            title="Komposisi Angsuran Bulanan",
            barmode='stack', bargap=0, template="plotly_dark", 
            height=300, margin=dict(l=0, r=0, t=40, b=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig_pinjaman, use_container_width=True)

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
# TAB 3: DASBOR PENGAJUAN DANA (PITCH DECK)
# ==========================================
with tab3:
    st.header(":red[Analisis Risiko Kredit & Kelayakan Arus Kas]")
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    saldo_akhir_tahun = st.session_state.modal_awal
    
    for thn in range(1, max_tahun + 1):
        # 1. Proyeksi Aset
        if thn == 1:
            aset_awal_tahun = st.session_state.modal_awal
        elif thn <= lama_investasi:
            aset_awal_tahun = saldo_akhir_tahun + st.session_state.tambahan_tahunan
        else:
            aset_awal_tahun = saldo_akhir_tahun
            
        saldo_akhir_tahun = aset_awal_tahun * (1 + st.session_state.dividen_tahun/100)
        profit_tahunan = saldo_akhir_tahun - aset_awal_tahun
        
        # 2. Proyeksi Hutang Tahunan
        bulan_mulai = (thn - 1) * 12
        bulan_akhir = min(thn * 12, tenor_bulan)
        
        if bulan_mulai < tenor_bulan:
            beban_tahunan = df_jadwal.iloc[bulan_mulai:bulan_akhir]["Total Angsuran"].sum()
            sisa_hutang = df_jadwal.iloc[bulan_akhir - 1]["Sisa Pinjaman"]
        else:
            beban_tahunan = 0
            sisa_hutang = 0
            
        data_cross.append([thn, saldo_akhir_tahun, sisa_hutang, profit_tahunan, beban_tahunan])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Total Aset", "Sisa Pokok Hutang", "Profit Tahunan", "Beban Cicilan Tahunan"])
    
    # --- GRAFIK 1: KEAMANAN AGUNAN (ASSET COVERAGE) ---
    st.subheader("1. Kurva Keamanan Aset (Asset Coverage vs Sisa Hutang)")
    st.write("Menunjukkan persilangan likuidasi. Titik potong (X) merepresentasikan tahun di mana portofolio dapat dilikuidasi untuk melunasi seluruh sisa pinjaman.")
    
    fig_aset = go.Figure()
    fig_aset.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Total Aset"], name="Total Nilai Portofolio (Aset)", line=dict(color='#00CC96', width=3.5)))
    fig_aset.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Sisa Pokok Hutang"], name="Sisa Pokok Pinjaman", line=dict(color='#EF553B', width=3.5)))
    
    fig_aset.update_layout(
        xaxis_title="Tahun Ke-", yaxis_title="Nominal (Rp)",
        hovermode="x unified", template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_aset, use_container_width=True)
    
    # --- GRAFIK 2: KEMANDIRIAN ARUS KAS (DEBT SERVICE COVERAGE) ---
    st.markdown("---")
    st.subheader("2. Kemandirian Arus Kas Tahunan (Debt Service Coverage)")
    st.write("Membandingkan Keuntungan murni per tahun (Gross Yield) terhadap Total Cicilan di tahun tersebut. Menunjukkan kapan investasi mulai membiayai pinjamannya sendiri (Self-Sustaining).")
    
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(x=df_cross["Tahun"], y=df_cross["Profit Tahunan"], name="Keuntungan Investasi Tahunan", marker_color='#00CC96', marker_line_width=0))
    fig_cf.add_trace(go.Bar(x=df_cross["Tahun"], y=df_cross["Beban Cicilan Tahunan"], name="Beban Cicilan Tahunan", marker_color='#EF553B', marker_line_width=0))
    
    fig_cf.update_layout(
        barmode='group', bargap=0.15, template="plotly_dark", height=400,
        xaxis_title="Tahun Ke-", yaxis_title="Nominal (Rp)",
        hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_cf, use_container_width=True)
    
    # --- RINGKASAN METRIK PENGAJUAN ---
    st.markdown("---")
    df_cross['Selisih Aset'] = df_cross['Total Aset'] - df_cross['Sisa Pokok Hutang']
    df_cross['Selisih CF'] = df_cross['Profit Tahunan'] - df_cross['Beban Cicilan Tahunan']
    
    titik_aset = df_cross[df_cross['Selisih Aset'] > 0]
    titik_cf = df_cross[df_cross['Selisih CF'] > 0]
    
    thn_aset = titik_aset.iloc[0]['Tahun'] if not titik_aset.empty else "Belum Tercapai"
    thn_cf = titik_cf.iloc[0]['Tahun'] if not titik_cf.empty else "Belum Tercapai"
    
    cm3, cm4 = st.columns(2)
    cm3.metric("Tahun Pelunasan Dini (Asset > Debt)", f"Tahun ke-{thn_aset}")
    cm4.metric("Tahun Mandiri Arus Kas (Profit > Cicilan)", f"Tahun ke-{thn_cf}")
