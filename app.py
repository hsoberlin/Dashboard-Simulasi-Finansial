import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title("📊 Dashboard Simulasi Finansial")

# Membuat dua tab terpisah
tab1, tab2 = st.tabs(["🏦 Kalkulator Pinjaman Anuitas", "📈 Simulasi Bunga Majemuk (Dividen)"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN ANUITAS
# ==========================================
with tab1:
    st.header("Kalkulator Pinjaman Anuitas")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Parameter Input")
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=10000000, value=1000000000, step=10000000, format="%d")
        bunga_tahun = st.number_input("Suku Bunga Tahunan (%)", min_value=1.0, value=8.10, step=0.1)
        tenor_bulan = st.slider("Tenor Pinjaman (Bulan)", min_value=12, max_value=360, value=180, step=12)
        
    with col2:
        # Perhitungan Anuitas Dasar
        bunga_bulan = (bunga_tahun / 100) / 12
        if bunga_bulan > 0:
            cicilan_per_bulan = plafon * (bunga_bulan * (1 + bunga_bulan)**tenor_bulan) / ((1 + bunga_bulan)**tenor_bulan - 1)
        else:
            cicilan_per_bulan = plafon / tenor_bulan
            
        st.subheader(f"Estimasi Cicilan: Rp {cicilan_per_bulan:,.0f} / bulan")
        
        # Membuat Jadwal Amortisasi
        saldo = plafon
        data_jadwal = []
        
        for bulan in range(1, tenor_bulan + 1):
            porsi_bunga = saldo * bunga_bulan
            porsi_pokok = cicilan_per_bulan - porsi_bunga
            saldo -= porsi_pokok
            data_jadwal.append([bulan, cicilan_per_bulan, porsi_pokok, porsi_bunga, max(0, saldo)])
            
        df_jadwal = pd.DataFrame(data_jadwal, columns=["Bulan", "Total Angsuran", "Porsi Pokok", "Porsi Bunga", "Sisa Pinjaman"])
        
        # Grafik Komposisi Pokok vs Bunga
        fig_pinjaman = go.Figure()
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Pokok"], name="Porsi Pokok", marker_color='#1F77B4'))
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Bunga"], name="Porsi Bunga", marker_color='#D62728'))
        
        fig_pinjaman.update_layout(
            title="Komposisi Angsuran Bulanan",
            barmode='stack',
            xaxis_title="Bulan Ke-",
            yaxis_title="Jumlah (Rp)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_pinjaman, use_container_width=True)
        
    # Menampilkan Tabel di bawah
    with st.expander("Tampilkan Tabel Detail Amortisasi"):
        st.dataframe(df_jadwal.style.format("{:,.0f}"))

# ==========================================
# TAB 2: SIMULASI BUNGA MAJEMUK (DIVIDEN)
# ==========================================
with tab2:
    st.header("Simulasi Bunga Majemuk (Dividen)")
    
    col3, col4 = st.columns([1, 3])
    
    with col3:
        st.subheader("Parameter Input")
        modal_awal = st.number_input("Modal Awal (Rp)", min_value=10000000, value=1000000000, step=10000000, format="%d", key="modal_dividen")
        dividen_tahun = st.number_input("Target Dividen Tahunan (%)", min_value=1.0, value=7.0, step=0.1)
        lama_investasi = st.slider("Lama Investasi (Tahun)", min_value=1, max_value=50, value=20, step=1)
        
    with col4:
        # Perhitungan Compound Interest
        data_investasi = []
        for tahun in range(1, lama_investasi + 1):
            total_nilai = modal_awal * (1 + (dividen_tahun / 100))**tahun
            akumulasi_dividen = total_nilai - modal_awal
            data_investasi.append([tahun, modal_awal, akumulasi_dividen, total_nilai])
            
        df_invest = pd.DataFrame(data_investasi, columns=["Tahun", "Modal Tetap", "Akumulasi Dividen", "Total Portofolio"])
        
        nilai_akhir = df_invest["Total Portofolio"].iloc[-1]
        st.subheader(f"Total Nilai Akhir: Rp {nilai_akhir:,.0f}")
        
        # Grafik Area Bertumpuk
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Modal Tetap"], mode='lines', stackgroup='one', name="Modal Tetap", fillcolor='#ABCDEF', line=dict(width=0)))
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Dividen"], mode='lines', stackgroup='one', name="Akumulasi Dividen", fillcolor='#FF9999', line=dict(width=0)))
        
        fig_invest.update_layout(
            title="Pertumbuhan Portofolio Berdasarkan Dividen",
            xaxis_title="Tahun Ke-",
            yaxis_title="Nilai Portofolio (Rp)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_invest, use_container_width=True)

    with st.expander("Tampilkan Tabel Detail Pertumbuhan"):
        st.dataframe(df_invest.style.format("{:,.0f}"))