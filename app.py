import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

st.set_page_config(page_title="Dashboard Finansial", layout="wide")
st.title("Dashboard Simulasi Finansial")

# --- INISIALISASI SESSION STATE ---
if 'modal_awal' not in st.session_state: st.session_state.modal_awal = 1000000000
if 'tambahan_tahunan' not in st.session_state: st.session_state.tambahan_tahunan = 0
if 'dividen_tahun' not in st.session_state: st.session_state.dividen_tahun = 7.0
if 'lama_investasi' not in st.session_state: st.session_state.lama_investasi = 20

tab1, tab2, tab3 = st.tabs(["Kalkulator Pinjaman", "Simulasi Investasi", "Analisis Leverage"])

# ==========================================
# TAB 1: KALKULATOR PINJAMAN
# ==========================================
with tab1:
    st.header("Kalkulator Pinjaman Berbasis Pasar")
    
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        st.subheader("Parameter")
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=1000000000, step=50000000, format="%d")
        tenor_bulan = st.slider("Tenor (Bulan)", min_value=12, max_value=360, value=240, step=12)
        tipe_bunga = st.radio("Tipe Bunga", ["Fixed", "Floating"])
        
        if tipe_bunga == "Fixed":
            bunga_tetap = st.number_input("Bunga Efektif (% p.a)", value=8.50, step=0.01)
        else:
            bunga_promo = st.number_input("Bunga Promo (% p.a)", value=6.00, step=0.01)
            masa_promo_thn = st.number_input("Lama Promo (Tahun)", value=3, step=1)
            bunga_floating = st.number_input("Bunga Floating (% p.a)", value=12.50, step=0.01)
            masa_promo_bln = masa_promo_thn * 12

    with col2:
        # Kalkulasi Data
        saldo = plafon
        data_jadwal = []
        
        if tipe_bunga == "Floating":
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

        for bulan in range(1, tenor_bulan + 1):
            if tipe_bunga == "Floating":
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
        
        total_pembayaran = df_jadwal["Total Angsuran"].sum()
        total_bunga = df_jadwal["Porsi Bunga"].sum()
        
        # Output Nilai Utama
        st.subheader("Ringkasan Kewajiban")
        m1, m2 = st.columns(2)
        m3, m4 = st.columns(2)
        
        m1.metric("1. Nilai Bayar Per Bulan (Angsuran)", f"Rp {df_jadwal.iloc[0]['Total Angsuran']:,.0f}")
        m2.metric("2. Total Bayar Hutang Sampai Lunas", f"Rp {total_pembayaran:,.0f}")
        m3.metric("3. Total Pokok Hutang", f"Rp {plafon:,.0f}")
        m4.metric("4. Total Beban Bunga", f"Rp {total_bunga:,.0f}")
        
        st.markdown("---")
        st.write("Tabel Rincian Pembayaran Per Bulan")
        st.dataframe(df_jadwal.style.format("Rp {:,.0f}"), use_container_width=True, height=250)

# ==========================================
# TAB 2: SIMULASI INVESTASI
# ==========================================
with tab2:
    st.header("Simulasi Investasi Bertahap")
    col3, col4 = st.columns([1, 2.5])
    
    with col3:
        st.session_state.modal_awal = st.number_input("Modal Awal (Rp)", value=st.session_state.modal_awal, step=10000000)
        st.session_state.tambahan_tahunan = st.number_input("Suntikan Tahunan (Rp)", value=st.session_state.tambahan_tahunan, step=5000000)
        st.session_state.dividen_tahun = st.number_input("Target Pertumbuhan (%)", value=st.session_state.dividen_tahun, step=0.1)
        st.session_state.lama_investasi = st.slider("Lama Investasi (Tahun)", 1, 50, st.session_state.lama_investasi)
        
    with col4:
        data_inv = []
        saldo_running = st.session_state.modal_awal
        total_modal_disetor = st.session_state.modal_awal
        
        for t in range(1, st.session_state.lama_investasi + 1):
            if t > 1: 
                saldo_running += st.session_state.tambahan_tahunan
                total_modal_disetor += st.session_state.tambahan_tahunan
            saldo_running *= (1 + st.session_state.dividen_tahun/100)
            profit_murni = saldo_running - total_modal_disetor
            data_inv.append([t, total_modal_disetor, profit_murni, saldo_running])
            
        df_invest = pd.DataFrame(data_inv, columns=["Tahun", "Total Modal Disetor", "Akumulasi Profit", "Total Portofolio"])
        st.metric("Total Nilai Portofolio Akhir", f"Rp {saldo_running:,.0f}")
        
        fig_invest = go.Figure()
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Total Modal Disetor"], mode='lines', stackgroup='one', name="Modal Disetor", fillcolor='#19D3F3', line=dict(width=0))) 
        fig_invest.add_trace(go.Scatter(x=df_invest["Tahun"], y=df_invest["Akumulasi Profit"], mode='lines', stackgroup='one', name="Akumulasi Profit", fillcolor='#AB63FA', line=dict(width=0))) 
        fig_invest.update_layout(template="plotly_dark", height=300, hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_invest, use_container_width=True)

# ==========================================
# TAB 3: ANALISIS LEVERAGE
# ==========================================
with tab3:
    st.header("Executive Summary: Profil Risiko & Pertumbuhan")
    
    max_tahun = max(math.ceil(tenor_bulan / 12), st.session_state.lama_investasi)
    data_cross = []
    saldo_akhir = st.session_state.modal_awal
    modal_total_disetor = st.session_state.modal_awal
    
    for thn in range(1, max_tahun + 1):
        if thn > 1 and thn <= st.session_state.lama_investasi:
            saldo_akhir += st.session_state.tambahan_tahunan
            modal_total_disetor += st.session_state.tambahan_tahunan
        saldo_akhir *= (1 + st.session_state.dividen_tahun/100)
        
        bulan_akhir = min(thn * 12, tenor_bulan)
        uang_cicilan = df_jadwal.iloc[:bulan_akhir]["Total Angsuran"].sum()
        sisa_hutang = df_jadwal.iloc[bulan_akhir - 1]["Sisa Pinjaman"] if bulan_akhir < tenor_bulan else 0
        
        total_uang_terbakar = modal_total_disetor + uang_cicilan
        akumulasi_margin = saldo_akhir - modal_total_disetor
        
        data_cross.append([thn, saldo_akhir, total_uang_terbakar, akumulasi_margin, sisa_hutang])

    df = pd.DataFrame(data_cross, columns=["Tahun", "Total Aset", "Total Uang Terbakar", "Margin Keuntungan", "Sisa Hutang"])
    
    df['Selisih_Aset_Terbakar'] = df['Total Aset'] - df['Total Uang Terbakar']
    df['Selisih_Margin_Hutang'] = df['Margin Keuntungan'] - df['Sisa Hutang']
    
    be_aset = df[df['Selisih_Aset_Terbakar'] > 0]
    thn_be_aset = be_aset.iloc[0]['Tahun'] if not be_aset.empty else "N/A"
    
    be_margin = df[df['Selisih_Margin_Hutang'] > 0]
    thn_be_margin = be_margin.iloc[0]['Tahun'] if not be_margin.empty else "N/A"

    st.write("Data-Driven Executive Summary")
    st.write(f"- Capital Protection: Nilai portofolio melampaui dana yang dibakar pada Tahun ke-{thn_be_aset}.")
    st.write(f"- Risk-Free Exit: Kapasitas melunasi pokok hutang menggunakan akumulasi margin tercapai pada Tahun ke-{thn_be_margin}.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Total Aset"], name="Total Nilai Aset", line=dict(color='#00CC96', width=3)))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Total Uang Terbakar"], name="Total Uang Terbakar", line=dict(color='#FFA15A', width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Margin Keuntungan"], name="Akumulasi Margin", line=dict(color='#636EFA', width=3)))
    fig.add_trace(go.Scatter(x=df["Tahun"], y=df["Sisa Hutang"], name="Sisa Pokok Hutang", line=dict(color='#EF553B', width=3)))
    
    fig.update_layout(template="plotly_dark", height=500, hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
