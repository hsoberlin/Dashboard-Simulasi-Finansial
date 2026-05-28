# ==========================================
# TAB 3: ANALISIS EKUITAS BERSIH (UPDATE FINAL)
# ==========================================
with tab3:
    st.header("Analisis Ekuitas: Nilai Aset vs Liabilitas vs Laba Bersih")
    st.write("Grafik ini memetakan pertumbuhan Total Aset, Sisa Hutang, Net Asset, serta Laba Bersih Kas (Pure Profit) setelah dikurangi seluruh pengeluaran kas aktual (modal investasi dan cicilan).")
    
    max_tahun = max(lama_investasi, math.ceil(tenor_bulan / 12))
    data_cross = []
    
    saldo_investasi_cross = 0
    total_modal_disetor_cross = 0
    akumulasi_cicilan_cross = 0
    
    for thn in range(1, max_tahun + 1):
        # 1. Total Nilai Aset & Modal Disetor
        if thn == 1:
            saldo_investasi_cross = modal_awal * (1 + (dividen_tahun / 100))
            total_modal_disetor_cross = modal_awal
        elif thn <= lama_investasi:
            saldo_investasi_cross = (saldo_investasi_cross + tambahan_tahunan) * (1 + (dividen_tahun / 100))
            total_modal_disetor_cross += tambahan_tahunan
        else:
            saldo_investasi_cross = saldo_investasi_cross * (1 + (dividen_tahun / 100))
            
        nilai_aset = saldo_investasi_cross
            
        # 2. Sisa Hutang & Akumulasi Setoran Bank
        bulan_berjalan = thn * 12
        batas_bulan = min(bulan_berjalan, tenor_bulan)
        
        if batas_bulan > 0:
            akumulasi_cicilan_cross = df_jadwal.loc[:batas_bulan-1, "Total Angsuran"].sum()
        else:
            akumulasi_cicilan_cross = 0

        if bulan_berjalan > tenor_bulan:
            sisa_hutang = 0
        else:
            sisa_hutang = df_jadwal.loc[bulan_berjalan - 1, "Sisa Pinjaman"]
        
        # 3. Net Asset (Aset - Hutang)
        net_asset = max(0, nilai_aset - sisa_hutang)
        
        # 4. Sunk Cost (Total uang yang dibakar: Modal Disetor + Cicilan Bank)
        sunk_cost = total_modal_disetor_cross + akumulasi_cicilan_cross
        
        # 5. Pure Profit (Laba Bersih Kas: Net Asset - Sunk Cost)
        pure_profit = net_asset - sunk_cost
        
        data_cross.append([thn, nilai_aset, sisa_hutang, net_asset, pure_profit])
        
    df_cross = pd.DataFrame(data_cross, columns=["Tahun", "Nilai Aset", "Sisa Hutang", "Net Asset", "Laba Bersih Kas"])
    
    fig_cross = go.Figure()
    
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Nilai Aset"], name="Total Aset", line=dict(color='#00CC96', width=3)))
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Sisa Hutang"], name="Sisa Hutang", line=dict(color='#EF553B', width=3)))
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Net Asset"], name="Net Asset (Ekuitas)", line=dict(color='#19D3F3', width=4, dash='dot')))
    fig_cross.add_trace(go.Scatter(x=df_cross["Tahun"], y=df_cross["Laba Bersih Kas"], name="Laba Bersih Kas", line=dict(color='#FFB703', width=4)))
    
    fig_cross.add_hline(y=0, line_width=1, line_dash="solid", line_color="white")
    
    fig_cross.update_layout(
        title="Kurva Kekayaan Bersih dan Break-Even Kas",
        xaxis_title="Tahun Ke-",
        yaxis_title="Nominal (Rp)",
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_cross, use_container_width=True)
    
    # Analisis Break-Even Kas Otomatis
    titik_breakeven = df_cross[df_cross['Laba Bersih Kas'] > 0]
    
    if not titik_breakeven.empty:
        tahun_be = titik_breakeven.iloc[0]['Tahun']
        st.info(f"Portofolio mencapai Absolute Break-Even pada Tahun ke-{tahun_be:.0f}. Pada titik ini, pertumbuhan aset telah menutupi seluruh uang kas aktual yang dikeluarkan (Sunk Cost).")
    else:
        st.warning("Laba Bersih Kas belum menembus angka positif hingga akhir periode simulasi. Secara akumulasi, uang yang dibakar masih lebih tinggi dari nilai Net Asset.")
