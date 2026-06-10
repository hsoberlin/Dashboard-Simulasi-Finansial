import streamlit as st
import pd as pd
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

st.set_page_config(page_title="Dashboard Finansial", layout="wide")

# --- CUSTOM CSS SMARTPHONE (PORTRAIT) & BLACK THEME ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #000000 !important; }
[data-testid="stHeader"] { background-color: transparent !important; }
p, h1, h2, h3, label, li, .stMarkdown, .stMetricLabel { color: #F8F9FA !important; }
@media (max-width: 768px) {
    h1 { font-size: 1.2rem !important; }
    h2 { font-size: 1.0rem !important; }
    h3 { font-size: 0.9rem !important; }
    p, label, li, .stMarkdown { font-size: 0.8rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.0rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
}
</style>
""", unsafe_allow_html=True)

st.title("Dashboard Simulasi Finansial")

# --- INISIALISASI SESSION STATE ---
if 'modal_awal' not in st.session_state: st.session_state.modal_awal = 450000000
if 'cicilan_tetap' not in st.session_state: st.session_state.cicilan_tetap = 0
if 'capex' not in st.session_state: st.session_state.capex = 200000000
if 'lama_simulasi' not in st.session_state: st.session_state.lama_simulasi = 15

tab1, tab2, tab3, tab4 = st.tabs(["Pinjaman", "Investasi Utama", "Arus Kas & Side Hustle", "Grand Analysis"])

# ==========================================
# TAB 1: PINJAMAN & CAPEX
# ==========================================
with tab1:
    st.header("Kalkulator Pinjaman")
    col1, col2 = st.columns([1, 2.5])
    with col1:
        plafon = st.number_input("Plafon Pinjaman (Rp)", min_value=0, value=650000000, step=50000000, format="%d")
        capex = st.number_input("Alokasi Capex", min_value=0, value=st.session_state.capex, step=10000000, format="%d")
        st.session_state.modal_awal = max(0, plafon - capex)
        tenor_bulan = st.slider("Tenor (Bulan)", 12, 180, 180, 12)
        bunga_tetap = st.number_input("Bunga Efektif (% p.a)", value=8.10, step=0.01)
    
    with col2:
        b_bln = (bunga_tetap/100)/12
        cicilan = (plafon * (b_bln * (1 + b_bln)**tenor_bulan) / ((1 + b_bln)**tenor_bulan - 1))
        st.session_state.cicilan_tetap = cicilan
        
        total_bunga = (cicilan * tenor_bulan) - plafon
        st.subheader("Beban Hutang")
        m1, m2 = st.columns(2)
        m1.metric("Cicilan / Bulan", f"Rp {cicilan:,.0f}")
        m2.metric("Total Bunga", f"Rp {total_bunga:,.0f}", delta=f"{(total_bunga/plafon)*100:.2f}% Total")

        # Tabel Sederhana Sisa Hutang untuk Tab 4
        data_hutang = []
        curr_saldo = plafon
        for b in range(1, tenor_bulan + 1):
            p_bunga = curr_saldo * b_bln
            p_pokok = cicilan - p_bunga
            curr_saldo -= p_pokok
            data_hutang.append(max(0, curr_saldo))
        df_sisa_hutang = pd.Series(data_hutang)

# ==========================================
# TAB 2: KANTONG 1 (INVESTASI UTAMA)
# ==========================================
with tab2:
    st.header("Kantong 1: Hasil Pinjaman")
    col_a, col_b = st.columns([1, 2.5])
    with col_a:
        roi_a = st.number_input("Target Pertumbuhan A (% p.a)", value=7.0, step=0.1)
    with col_b:
        st.metric("Modal Kerja", f"Rp {st.session_state.modal_awal:,.0f}")
        data_k1 = []
        saldo_k1 = st.session_state.modal_awal
        for th in range(1, 16):
            saldo_k1 *= (1 + roi_a/100)
            data_k1.append(saldo_k1)
        st.caption("Investasi ini murni dari sisa plafon bank.")

# ==========================================
# TAB 3: ARUS KAS & SIDE HUSTLE (KANTONG 2)
# ==========================================
with tab3:
    st.header("Manajemen Arus Kas & Side Hustle")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("Gaji & Pengeluaran")
        gaji = st.number_input("Gaji Bulanan (Rp)", value=20000000, step=1000000)
        naik_gaji = st.slider("Kenaikan Gaji / Thn (%)", 0, 20, 5)
        potongan_lain = st.number_input("Potongan Pinjaman Lain (Rp)", value=0)
        biaya_hidup = st.number_input("Kebutuhan Hidup (Rp)", value=10000000, step=500000)
        inflasi_biaya = st.slider("Inflasi Biaya Hidup (%)", 0, 20, 3)

    with c2:
        st.subheader("Side Hustle (Tahunan)")
        sh1 = st.number_input("Side Hustle 1", value=0)
        sh2 = st.number_input("Side Hustle 2", value=0)
        sh3 = st.number_input("Side Hustle 3", value=0)
        sh4 = st.number_input("Side Hustle 4", value=0)
        sh5 = st.number_input("Side Hustle 5", value=0)
        roi_b = st.number_input("Target Pertumbuhan B (% p.a)", value=10.0)

    # Logika Perhitungan Proyeksi Arus Kas
    data_k2 = []
    data_emergency = []
    saldo_k2 = 0
    total_emergency = 0
    
    # Loop Proyeksi 15 Tahun
    list_proyeksi = []
    for t in range(1, 16):
        gaji_t = gaji * ((1 + naik_gaji/100)**(t-1))
        biaya_t = biaya_hidup * ((1 + inflasi_biaya/100)**(t-1))
        cicilan_t = st.session_state.cicilan_tetap if t <= (tenor_bulan/12) else 0
        
        sisa_gaji = gaji_t - (potongan_lain + cicilan_t)
        sisa_bersih_bln = sisa_gaji - biaya_t
        
        # Poin g & j (Emergency 50%)
        total_sh = sh1 + sh2 + sh3 + sh4 + sh5
        emergency_thn = (sisa_bersih_bln * 12 * 0.5) + (total_sh * 0.5)
        invest_thn = (sisa_bersih_bln * 12 * 0.5) + (total_sh * 0.5)
        
        # Kantong 2 dimulai tahun ke-2 (sesuai rencana Anda)
        if t >= 2:
            saldo_k2 = (saldo_k2 + invest_thn) * (1 + roi_b/100)
        else:
            saldo_k2 = 0
            
        total_emergency += emergency_thn
        data_k2.append(saldo_k2)
        data_emergency.append(total_emergency)
        
        list_proyeksi.append([t, gaji_t, sisa_bersih_bln, total_sh, saldo_k2, total_emergency])

    df_proyeksi = pd.DataFrame(list_proyeksi, columns=["Thn", "Gaji", "Sisa/Bln", "SideHustle", "Kantong 2", "Total Emergency"])
    st.subheader("Proyeksi Tabungan & Emergency")
    st.dataframe(df_proyeksi.style.format("Rp {:,.0f}"), use_container_width=True)

# ==========================================
# TAB 4: GRAND ANALYSIS (TOTAL LEVERAGE)
# ==========================================
with tab4:
    st.header("Total Net Worth (Kantong 1 + Kantong 2)")
    
    data_final = []
    for i in range(15):
        th = i + 1
        idx_bln = min((th * 12) - 1, len(df_sisa_hutang)-1)
        s_hutang = df_sisa_hutang.iloc[idx_bln] if th <= (tenor_bulan/12) else 0
        
        aset_k1 = data_k1[i]
        aset_k2 = data_k2[i]
        total_aset = aset_k1 + aset_k2
        net_worth = total_aset - s_hutang
        
        data_final.append([th, aset_k1, aset_k2, total_aset, s_hutang, net_worth])
    
    df_final = pd.DataFrame(data_final, columns=["Tahun", "Kantong 1", "Kantong 2", "Total Aset", "Sisa Hutang", "Kekayaan Bersih"])
    
    m_a, m_b = st.columns(2)
    m_a.metric("Total Aset (Tahun 15)", f"Rp {df_final.iloc[-1]['Total Aset']:,.0f}")
    m_b.metric("Kekayaan Bersih Akhir", f"Rp {df_final.iloc[-1]['Kekayaan Bersih']:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_final["Tahun"], y=df_final["Total Aset"], name="Total Aset Gabungan", line=dict(color='#00CC96', width=4)))
    fig.add_trace(go.Scatter(x=df_final["Tahun"], y=df_final["Kekayaan Bersih"], name="Net Worth (Bebas Hutang)", line=dict(color='#FFFFFF', width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=df_final["Tahun"], y=df_final["Sisa Hutang"], name="Sisa Hutang Bank", line=dict(color='#EF553B', width=2)))
    
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Kantong 2 (Side Hustle) mulai berkontribusi signifikan pada pertumbuhan aset di tahun ke-2.")
