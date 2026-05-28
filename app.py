import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

# Membuat tiga tab terpisah
tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman Anuitas", "Simulasi Bunga Majemuk", "Analisis Ekuitas Bersih"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN ANUITAS
# ==========================================
with tab1:
    st.header(":orange[Kalkulator Pinjaman Anuitas]")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Parameter Input")
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=1000000000, step=50000000, format="%d")
        bunga_tahun = st.number_input("Suku Bunga Tahunan (%)", min_value=1.00, value=8.10, step=0.01, format="%.2f")
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
        modal_awal = st.number_input("Modal Awal (Rp)", min_value=0, value=1000000000, step=1000000, format="%d", key="modal_dividen")
        tambahan_tahunan = st.number_input("Tambahan Investasi per Tahun (Mulai Thn ke-2)", min_value=0, value=0, step=10000000, format="%d")
        dividen_tahun = st.number_input("Target Dividen Tahunan (%)", min_value=1.0, value=7.0, step=0.1, format="%.1f")
        lama_investasi = st.slider("Lama Investasi (Tahun)", min_value=1, max_value=50, value=20, step=1)
        
    with col4:
        data_investasi = []
        saldo_investasi = 0
        total_modal_disetor = 0
        
        for tahun in range(1, lama_investasi + 1):
            if tahun == 1:
                total_modal_disetor = modal_awal
                saldo_investasi = modal_awal * (1 + (dividen_tahun / 100))
            else:
                total_modal_disetor += tambahan_tahunan
                saldo_investasi = (saldo_investasi + tambahan_tahunan) * (1 + (dividen_tahun / 100))
                
            akumulasi_dividen = saldo_investasi - total_modal_disetor
            data_investasi.append([tahun, total_modal_disetor, akumulasi_dividen, saldo_investasi])
            
        df_invest = pd.DataFrame(data_investasi, columns=["Tahun", "Total Modal Disetor", "Akumulasi Dividen", "Total Portofolio"])
        
        nilai_akhir = df_invest["Total Portofolio"].iloc[-1]
        st.subheader(f"Total Nilai Akhir: :green[Rp {nilai_akhir:,.0f}]")
        
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Total Modal Disetor"], mode='lines', stackgroup='one', name="Total Modal Disetor", fillcolor='#19D3F3', line=dict(width=0))) 
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Dividen"], mode='lines', stackgroup='one', name="Akumulasi Dividen", fillcolor='#AB63FA', line=dict(width=0))) 
        
        fig_invest.update_layout(
            title="Pertumbuhan Portofolio Berdasarkan Dividen & Top-Up",
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
    st.header(":red[Analisis Ekuitas: Nilai Aset vs Sisa Hutang]")
    st.write("Grafik ini mengukur posisi 'Net Worth' (Kekayaan Bersih) Anda. Titik temu terjadi ketika pertumbuhan Total Aset Portofolio Anda resmi melampaui Sisa Pokok Pinjaman di bank.")
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    saldo_investasi_cross = 0
    
    for thn in range(1, max_tahun + 1):
        # 1. Menghitung Total Nilai Aset (Iteratif dengan Top-Up)
        if thn == 1:
            saldo_investasi_cross = modal_awal * (1 + (dividen_tahun / 100))
        elif thn <= lama_investasi:
            saldo_investasi_cross = (saldo_investasi_cross + tambahan_tahunan) * (1 + (dividen_tahun / 100))
        else:
            # Jika melebihi masa investasi, diasumsikan uang tetap mengendap dan berbunga tanpa top-up baru
            saldo_investasi_cross = saldo_investasi_cross * (1 + (dividen_tahun / 100))
            
        nilai_aset = saldo_investasi_cross
            
        # 2. Menghitung Sisa Pokok Pinjaman di Akhir Tahun Tersebut
        bulan_berjalan = min(thn * 12, tenor_bulan)
        if bulan_berjalan == tenor_bulan:
            sisa_hutang = 0
        else:
            if bunga_bulan > 0:
                sisa_hutang = plafon * (((1 + bunga_bulan)**tenor_bulan - (1 + bunga_bulan)**bulan_berjalan) / ((1 + bunga_bulan)**tenor_bulan - 1))
            else:
                sisa_hutang = max(0, plafon - (cicilan_per_bulan * bulan_berjalan))
        
        data_cross.append([thn, nilai_aset, sisa_hutang])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Nilai Aset", "Sisa Hutang"])
    
    fig_cross = go.Figure()
    
    fig_cross.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["Nilai Aset"], 
        mode='lines+markers', name="Total Nilai Aset", 
        line=dict(color='#00CC96', width=3)
    ))
    
    fig_cross.add_trace(go.Scatter(
        x=df_cross["Tahun"], y=df_cross["Sisa Hutang"], 
        mode='lines+markers', name="Sisa Pokok Pinjaman", 
        line=dict(color='#EF553B', width=3)
    ))
    
    fig_cross.update_layout(
        title="Kurva Kekayaan Bersih (Aset vs Liabilitas)",
        xaxis_title="Tahun Ke-",
        yaxis_title="Nominal (Rp)",
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_cross, use_container_width=True)
    
    df_cross['Net Worth'] = df_cross['Nilai Aset'] - df_cross['Sisa Hutang']
    titik_temu = df_cross[df_cross['Net Worth'] > 0]
    
    if not titik_temu.empty:
        tahun_temu = titik_temu.iloc[0]['Tahun']
        st.success(f"Berdasarkan parameter saat ini, portofolio Anda mencapai **Ekuitas Positif** pada **Tahun ke-{tahun_temu:.0f}**. Pada titik ini, nilai aset Anda sudah lebih besar daripada sisa hutang bank Anda, sehingga secara teknikal Anda sudah bisa melunasi seluruh hutang tersebut menggunakan aset investasi jika diperlukan.")
    else:
        st.warning("Dengan parameter saat ini, nilai aset Anda belum berhasil melampaui sisa hutang hingga akhir periode simulasi.")
