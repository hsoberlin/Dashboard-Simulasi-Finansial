import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# Pengaturan dasar halaman
st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title(":blue[Dashboard Simulasi Finansial]")

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
        st.subheader("Parameter Institusi")
        kategori_bank = st.selectbox("Pilih Institusi Perbankan", list(db_bank.keys()))
        jenis_kredit = st.selectbox("Jenis Fasilitas Kredit", list(db_bank[kategori_bank].keys()))
        data_kredit = db_bank[kategori_bank][jenis_kredit]
        
        st.markdown("---")
        st.subheader("Parameter Pinjaman")
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=1000000000, step=50000000, format="%d")
        tenor_bulan = st.slider("Tenor Pinjaman (Bulan)", min_value=12, max_value=360, value=240, step=12)
        
        # Logika UI Dinamis berdasarkan tipe kredit
        if data_kredit["tipe"] == "floating":
            bunga_promo = st.number_input("Suku Bunga Promo Awal (% p.a)", min_value=1.00, value=data_kredit["promo"], step=0.01, format="%.2f")
            masa_promo_thn = st.number_input("Lama Masa Promo (Tahun)", min_value=1, max_value=10, value=3, step=1)
            bunga_floating = st.number_input("Suku Bunga Floating (% p.a)", min_value=1.00, value=data_kredit["floating"], step=0.01, format="%.2f")
            masa_promo_bln = masa_promo_thn * 12
        else:
            bunga_tetap = st.number_input("Suku Bunga Efektif (% p.a)", min_value=1.00, value=data_kredit["rate"], step=0.01, format="%.2f")
            
    with col2:
        saldo = plafon
        data_jadwal = []
        cicilan_saat_ini = 0
        
        # Logika Perhitungan Amortisasi (Fixed vs Floating)
        if data_kredit["tipe"] == "floating":
            for bulan in range(1, tenor_bulan + 1):
                sisa_tenor = tenor_bulan - bulan + 1
                
                # Fase Promo
                if bulan <= masa_promo_bln:
                    bunga_bln = (bunga_promo / 100) / 12
                    if bulan == 1:
                        if bunga_bln > 0:
                            cicilan_tetap = saldo * (bunga_bln * (1 + bunga_bln)**sisa_tenor) / ((1 + bunga_bln)**sisa_tenor - 1)
                        else:
                            cicilan_tetap = saldo / sisa_tenor
                    cicilan_saat_ini = cicilan_tetap
                
                # Fase Floating (Rekalkulasi)
                else:
                    bunga_bln = (bunga_floating / 100) / 12
                    if bulan == masa_promo_bln + 1:
                        if bunga_bln > 0:
                            cicilan_floating = saldo * (bunga_bln * (1 + bunga_bln)**sisa_tenor) / ((1 + bunga_bln)**sisa_tenor - 1)
                        else:
                            cicilan_floating = saldo / sisa_tenor
                    cicilan_saat_ini = cicilan_floating
                    
                porsi_bunga = saldo * bunga_bln
                porsi_pokok = cicilan_saat_ini - porsi_bunga
                saldo -= porsi_pokok
                data_jadwal.append([bulan, cicilan_saat_ini, porsi_pokok, porsi_bunga, max(0, saldo)])
                
            st.subheader(f"Estimasi Cicilan Promo: :green[Rp {cicilan_tetap:,.0f}] / bulan")
            st.subheader(f"Estimasi Cicilan Floating (Bulan ke-{masa_promo_bln + 1}): :red[Rp {cicilan_floating:,.0f}] / bulan")
            
        else:
            bunga_bln = (bunga_tetap / 100) / 12
            if bunga_bln > 0:
                cicilan_saat_ini = plafon * (bunga_bln * (1 + bunga_bln)**tenor_bulan) / ((1 + bunga_bln)**tenor_bulan - 1)
            else:
                cicilan_saat_ini = plafon / tenor_bulan
                
            st.subheader(f"Estimasi Cicilan Tetap: :green[Rp {cicilan_saat_ini:,.0f}] / bulan")
            
            for bulan in range(1, tenor_bulan + 1):
                porsi_bunga = saldo * bunga_bln
                porsi_pokok = cicilan_saat_ini - porsi_bunga
                saldo -= porsi_pokok
                data_jadwal.append([bulan, cicilan_saat_ini, porsi_pokok, porsi_bunga, max(0, saldo)])
                
        # Konversi ke DataFrame
        df_jadwal = pd.DataFrame(data_jadwal, columns=["Bulan", "Total Angsuran", "Porsi Pokok", "Porsi Bunga", "Sisa Pinjaman"])
        
        # Visualisasi Grafik
        fig_pinjaman = go.Figure()
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Pokok"], name="Porsi Pokok", marker_color='#00CC96')) 
        fig_pinjaman.add_trace(go.Bar(x=df_jadwal["Bulan"], y=df_jadwal["Porsi Bunga"], name="Porsi Bunga", marker_color='#EF553B')) 
        
        # Tambahan garis bantu untuk menyoroti perubahan cicilan jika floating
        if data_kredit["tipe"] == "floating":
            fig_pinjaman.add_vline(x=masa_promo_bln, line_width=2, line_dash="dash", line_color="white", annotation_text="Akhir Promo", annotation_position="top right")

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
    st.header(":violet[Simulasi Investasi Bertahap]")
    
    col3, col4 = st.columns([1, 3])
    
    with col3:
        st.subheader("Parameter Investasi")
        modal_awal = st.number_input("Modal Awal (Rp)", min_value=0, value=1000000000, step=1000000, format="%d", key="modal_dividen")
        tambahan_tahunan = st.number_input("Suntikan Dana per Tahun (Mulai Thn ke-2)", min_value=0, value=0, step=10000000, format="%d")
        dividen_tahun = st.number_input("Target Pertumbuhan Tahunan (%)", min_value=1.0, value=7.0, step=0.1, format="%.1f")
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
            
        df_invest = pd.DataFrame(data_investasi, columns=["Tahun", "Total Modal Disetor", "Akumulasi Dividen (Profit)", "Total Portofolio"])
        
        nilai_akhir = df_invest["Total Portofolio"].iloc[-1]
        st.subheader(f"Total Nilai Akhir: :green[Rp {nilai_akhir:,.0f}]")
        
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Total Modal Disetor"], mode='lines', stackgroup='one', name="Total Modal Disetor", fillcolor='#19D3F3', line=dict(width=0))) 
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Dividen (Profit)"], mode='lines', stackgroup='one', name="Akumulasi Profit", fillcolor='#AB63FA', line=dict(width=0))) 
        
        fig_invest.update_layout(
            title="Pertumbuhan Portofolio Berdasarkan Dividen & Top-Up Tahunan",
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
    st.header(":red[Analisis Ekuitas: Total Aset vs Sisa Hutang]")
    st.write("Grafik ini menarik data langsung dari tabel amortisasi dan tabel investasi untuk mengukur posisi Kekayaan Bersih (Net Worth). Titik temu terjadi ketika Total Aset melampaui Sisa Pokok Pinjaman yang berjalan.")
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    saldo_investasi_cross = 0
    
    for thn in range(1, max_tahun + 1):
        # 1. Mengambil Proyeksi Aset Investasi
        if thn == 1:
            saldo_investasi_cross = modal_awal * (1 + (dividen_tahun / 100))
        elif thn <= lama_investasi:
            saldo_investasi_cross = (saldo_investasi_cross + tambahan_tahunan) * (1 + (dividen_tahun / 100))
        else:
            saldo_investasi_cross = saldo_investasi_cross * (1 + (dividen_tahun / 100))
            
        nilai_aset = saldo_investasi_cross
            
        # 2. Mengambil Sinkronisasi Sisa Hutang dari DataFrame Tab 1
        bulan_berjalan = thn * 12
        if bulan_berjalan > tenor_bulan:
            sisa_hutang = 0
        else:
            # Pandas menggunakan index mulai dari 0, sehingga bulan ke-12 ada di index 11
            sisa_hutang = df_jadwal.loc[bulan_berjalan - 1, "Sisa Pinjaman"]
        
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
        title="Kurva Kekayaan Bersih (Total Aset vs Kewajiban Institusi)",
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
        st.success(f"Portofolio mencapai **Ekuitas Positif** pada **Tahun ke-{tahun_temu:.0f}**. Secara teknikal, likuidasi aset di titik ini mampu menutup penuh sisa hutang institusi yang sedang berjalan.")
    else:
        st.warning("Nilai aset belum berhasil melampaui sisa hutang hingga akhir periode simulasi.")
