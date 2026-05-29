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

tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Institusi", "Simulasi Investasi Bertahap", "Analisis PnL Kas"])

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
        
        total_pembayaran_kredit = df_jadwal["Total Angsuran"].sum()
        total_beban_bunga = df_jadwal["Porsi Bunga"].sum()
        
        st.subheader(f"Total Kewajiban Pinjaman Hingga Lunas: :red[Rp {total_pembayaran_kredit:,.0f}]")
        
        cm1, cm2 = st.columns(2)
        cm1.metric("Total Pokok Hutang", f"Rp {plafon:,.0f}")
        cm2.metric("Total Biaya Bunga (Cost of Credit)", f"Rp {total_beban_bunga:,.0f}")
        
        # PERBAIKAN VISUAL TAB 1: Hilangkan garis tepi (marker_line_width=0) dan gap (bargap=0)
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
            barmode='stack', bargap=0, template="plotly_dark", 
            height=300, margin=dict(l=0, r=0, t=30, b=0)
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
        st.line_chart(df_invest.set_index("Tahun")[["Total Modal Disetor", "Total Portofolio"]])

# ==========================================
# TAB 3: ANALISIS PnL KAS (Garis Nol)
# ==========================================
with tab3:
    st.header(":red[Kurva Profit & Loss Aktual (Cash-on-Cash)]")
    st.write("Grafik ini menunjukkan Laba Bersih Murni (PnL) yang dihitung dengan mengurangi **Total Nilai Investasi** dengan **Total Uang yang Dibakar** (Modal Disetor + Akumulasi Cicilan Bank).")
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    saldo_cross = st.session_state.modal_awal
    modal_disetor_cross = st.session_state.modal_awal
    
    for thn in range(1, max_tahun + 1):
        if thn > 1 and thn <= lama_investasi:
            saldo_cross += st.session_state.tambahan_tahunan
            modal_disetor_cross += st.session_state.tambahan_tahunan
            
        saldo_cross *= (1 + st.session_state.dividen_tahun/100)
        total_nilai_investasi = saldo_cross
        
        bulan_berjalan = min(thn * 12, tenor_bulan)
        if bulan_berjalan > 0:
            uang_cicilan = df_jadwal.head(bulan_berjalan)["Total Angsuran"].sum()
        else:
            uang_cicilan = df_jadwal["Total Angsuran"].sum()
            
        total_uang_dibakar = modal_disetor_cross + uang_cicilan
        pnl_kas = total_nilai_investasi - total_uang_dibakar
        
        data_cross.append([thn, total_nilai_investasi, total_uang_dibakar, pnl_kas])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Total Aset", "Sunk Cost", "PnL"])
    
    # PERBAIKAN VISUAL TAB 3: Dinamisasi Warna Area Berdasarkan Profit/Loss
    fig_pnl = go.Figure()
    
    # Memisahkan data positif dan negatif untuk gradien yang lebih intuitif
    df_cross['PnL_Positif'] = df_cross['PnL'].apply(lambda x: x if x >= 0 else None)
    df_cross['PnL_Negatif'] = df_cross['PnL'].apply(lambda x: x if x < 0 else None)
    
    # Trace Area Negatif (Merah)
    fig_pnl.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["PnL_Negatif"], 
        mode='lines', name="Fase Drawdown (Loss)", 
        line=dict(color='#EF553B', width=3),
        fill='tozeroy', fillcolor='rgba(239, 85, 59, 0.2)'
    ))
    
    # Trace Area Positif (Hijau)
    fig_pnl.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["PnL_Positif"], 
        mode='lines', name="Fase Profit (Break-Even)", 
        line=dict(color='#00CC96', width=3),
        fill='tozeroy', fillcolor='rgba(0, 204, 150, 0.2)'
    ))
    
    fig_pnl.add_hline(y=0, line_width=2, line_dash="solid", line_color="white")
    
    fig_pnl.update_layout(
        title="Kurva Absolute Break-Even (Kapan Portofolio Mengalahkan Sunk Cost?)",
        xaxis_title="Tahun Ke-",
        yaxis_title="Nominal PnL (Rp)",
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig_pnl, use_container_width=True)
    
    titik_temu = df_cross[df_cross['PnL'] > 0]
    
    if not titik_temu.empty:
        tahun_be = titik_temu.iloc[0]['Tahun']
        st.success(f"Portofolio berhasil mencetak **Net-Positive (PnL > 0)** pada **Tahun ke-{tahun_be:.0f}**. Sejak titik ini, seluruh uang yang Anda keluarkan (Modal + Cicilan Bank) sudah impas dan tergantikan penuh oleh pertumbuhan aset.")
    else:
        st.warning("Hingga akhir periode simulasi, pertumbuhan portofolio belum mampu menutupi akumulasi seluruh modal dan cicilan bank (PnL masih negatif).")

    with st.expander("Tampilkan Rekap Data PnL per Tahun"):
        st.dataframe(df_cross.style.format("{:,.0f}"))
