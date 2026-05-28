import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman (Tanpa simbol)
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

# Membuat tiga tab terpisah
tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Anuitas", "Simulasi Bunga Majemuk", "Analisis Titik Temu"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN ANUITAS
# ==========================================
with tab1:
    st.header(":orange[Kalkulator Pinjaman Anuitas]")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Parameter Input")
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=1000000000, step=1, format="%d")
        bunga_tahun = st.number_input("Suku Bunga Tahunan (%)", min_value=1.0, value=8.10, step=0.1)
        tenor_bulan = st.slider("Tenor Pinjaman (Bulan)", min_value=12, max_value=360, value=240, step=12)
        
    with col2:
        bunga_bulan = (bunga_tahun / 100) / 12
        if bunga_bulan > 0:
            cicilan_per_bulan = plafon * (bunga_bulan * (1 + bunga_bulan)**tenor_bulan) / ((1 + bunga_bulan)**tenor_bulan - 1)
        else:
            cicilan_per_bulan = plafon / tenor_bulan
            
        st.subheader(f"Estimasi Cicilan: :green[Rp {cicilan_per_bulan:,.0f}] / bulan")
        
        saldo = plafon
        data_jadwal = []
        
        for bulan in range(1, tenor_bulan + 1):
            porsi_bunga = saldo * bunga_bulan
            porsi_pokok = cicilan_per_bulan - porsi_bunga
            saldo -= porsi_pokok
            data_jadwal.append([bulan, cicilan_per_bulan, porsi_pokok, porsi_bunga, max(0, saldo)])
            
        df_jadwal = pd.DataFrame(data_jadwal, columns=["Bulan", "Total Angsuran", "Porsi Pokok", "Porsi Bunga", "Sisa Pinjaman"])
        
        fig_pinjaman = go.Figure()
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Pokok"], name="Porsi Pokok", marker_color='#00CC96')) 
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Bunga"], name="Porsi Bunga", marker_color='#EF553B')) 
        
        fig_pinjaman.update_layout(
            title="Komposisi Angsuran Bulanan",
            barmode='stack',
            xaxis_title="Bulan Ke-",
            yaxis_title="Jumlah (Rp)",
            hovermode="x unified",
            template="plotly_dark",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_pinjaman, use_container_width=True)
        
    with st.expander("Tampilkan Tabel Detail Amortisasi"):
        st.dataframe(df_jadwal.style.format("{:,.0f}"))

# ==========================================
# TAB 2: SIMULASI BUNGA MAJEMUK
# ==========================================
with tab2:
    st.header(":violet[Simulasi Bunga Majemuk]")
    
    col3, col4 = st.columns([1, 3])
    
    with col3:
        st.subheader("Parameter Input")
        modal_awal = st.number_input("Modal Awal (Rp)", min_value=0, value=1000000000, step=1, format="%d", key="modal_dividen")
        dividen_tahun = st.number_input("Target Dividen Tahunan (%)", min_value=1.0, value=7.0, step=0.1)
        lama_investasi = st.slider("Lama Investasi (Tahun)", min_value=1, max_value=50, value=20, step=1)
        
    with col4:
        data_investasi = []
        for tahun in range(1, lama_investasi + 1):
            total_nilai = modal_awal * (1 + (dividen_tahun / 100))**tahun
            akumulasi_dividen = total_nilai - modal_awal
            data_investasi.append([tahun, modal_awal, akumulasi_dividen, total_nilai])
            
        df_invest = pd.DataFrame(data_investasi, columns=["Tahun", "Modal Tetap", "Akumulasi Dividen", "Total Portofolio"])
        
        nilai_akhir = df_invest["Total Portofolio"].iloc[-1]
        st.subheader(f"Total Nilai Akhir: :green[Rp {nilai_akhir:,.0f}]")
        
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Modal Tetap"], mode='lines', stackgroup='one', name="Modal Tetap", fillcolor='#19D3F3', line=dict(width=0))) 
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Dividen"], mode='lines', stackgroup='one', name="Akumulasi Dividen", fillcolor='#AB63FA', line=dict(width=0))) 
        
        fig_invest.update_layout(
            title="Pertumbuhan Portofolio Berdasarkan Dividen",
            xaxis_title="Tahun Ke-",
            yaxis_title="Nilai Portofolio (Rp)",
            hovermode="x unified",
            template="plotly_dark",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_invest, use_container_width=True)

    with st.expander("Tampilkan Tabel Detail Pertumbuhan"):
        st.dataframe(df_invest.style.format("{:,.0f}"))

# ==========================================
# TAB 3: ANALISIS TITIK TEMU (CROSSOVER)
# ==========================================
with tab3:
    st.header(":red[Analisis Persilangan: Investasi vs Beban Pinjaman]")
    st.write("Grafik ini mengukur momentum kapan nilai aset investasi Anda berhasil memotong dan melampaui total akumulasi dana kas yang telah Anda bayarkan ke bank.")
    
    # Menentukan batas sumbu X agar pas dengan tenor atau investasi terlama
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    for thn in range(1, max_tahun + 1):
        # 1. Menghitung Pertumbuhan Investasi
        if thn <= lama_investasi:
            nilai_investasi = modal_awal * (1 + (dividen_tahun / 100))**thn
        else:
            nilai_investasi = modal_awal * (1 + (dividen_tahun / 100))**lama_investasi
            
        # 2. Menghitung Akumulasi Beban Pinjaman (Cash Outflow)
        bulan_berjalan = min(thn * 12, tenor_bulan)
        akumulasi_cicilan = bulan_berjalan * cicilan_per_bulan
        
        data_cross.append([thn, nilai_investasi, akumulasi_cicilan])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Nilai Investasi", "Akumulasi Pembayaran"])
    
    # Menggambar Grafik 2 Garis
    fig_cross = go.Figure()
    
    # Garis Investasi (Hijau)
    fig_cross.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["Nilai Investasi"], 
        mode='lines+markers', name="Nilai Investasi (Aset)", 
        line=dict(color='#00CC96', width=3)
    ))
    
    # Garis Pinjaman (Merah)
    fig_cross.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["Akumulasi Pembayaran"], 
        mode='lines+markers', name="Total Setoran ke Bank (Beban)", 
        line=dict(color='#EF553B', width=3)
    ))
    
    fig_cross.update_layout(
        title="Kurva Arbitrase (Titik Temu Break-Even)",
        xaxis_title="Tahun Ke-",
        yaxis_title="Nominal (Rp)",
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_cross, use_container_width=True)
    
    # Analisis Otomatis
    df_cross['Selisih'] = df_cross['Nilai Investasi'] - df_cross['Akumulasi Pembayaran']
    titik_temu = df_cross[df_cross['Selisih'] > 0]
    
    if not titik_temu.empty:
        tahun_temu = titik_temu.iloc[0]['Tahun']
        st.success(f"Berdasarkan parameter saat ini, strategi ini mulai mencetak **Net-Positive (Keuntungan Bersih)** pada **Tahun ke-{tahun_temu:.0f}**. Pada titik ini, nilai investasi Anda sudah melampaui seluruh uang yang Anda setorkan untuk cicilan.")
    else:
        st.warning("Dengan parameter saat ini, garis investasi belum berhasil memotong garis akumulasi pinjaman hingga akhir periode. Pertimbangkan untuk mencari instrumen dengan dividen lebih tinggi atau mempercepat tenor.")
