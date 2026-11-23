"""
R2 ENGINE — akun OBERLIN
================================================================
Aturan R2 + peringatan kas (final 21–22 Nov 2026). Turunan trendline v1.2.
Sinyal, SL, hold, jual, pagar jual, suspensi = trendline v1.2 (inti disalin apa adanya).

1. Sinyal malam -> beli Rp1 jt market order di open besok.
2. Malam SL naik -> tambah Rp1,5 jt market order, maksimal Rp15 jt per saham.
3. Kas kurang -> sinyal baru didahulukan, baru tambahan.
4. ARA terkunci / suspensi -> order diulang besok di close baru (sinyal baru batal kalau close < SL awal).
5. SL / hold / jual ikut trendline v1.2 (jual market order di open setelah close < SL).
6. Setor: perkiraan 3 hari = 3 x p90 kebutuhan order harian 60 hari terakhir. Kas bebas + setoran
   dalam perjalanan di bawah itu -> setor selisihnya, dianggap masuk 3 hari bursa kemudian.
7. Tarik: kas menganggur > 50% ekuitas selama 20 hari bursa -> tarik kelebihan di atas perkiraan
   tertinggi 120 hari, maksimal sebesar total setoran (modal awal & untung tidak ditarik).
Dana dikunci market order Stockbit = lot x harga batas ARA x (1 + fee beli).
Fee beli 0,15%, jual 0,25%, materai Rp10.000 per hari kalau transaksi > Rp10 jt.
Laporan mekanis: dianggap semua perintah dijalankan penuh.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

VERSION = "R2 (22 Nov 2026)"
AKUN = "OBERLIN"
START_DATA = "2019-01-01"
FIRST, LAPIS, CAP = 1_000_000, 1_500_000, 15_000_000
LEAD, HPROJ, Q = 3, 60, 90
IDLE_W, IDLE_DAYS, FLOOR_LB, TARIK_MIN = 0.5, 20, 120, 1_000_000
LIBUR = {"2026-12-24", "2026-12-25", "2026-12-31", "2027-01-01"}   # libur bursa (tambah daftar 2027 saat terbit)
IHSG_RET = None

IDX_TICKERS_ALL = """AADI, AALI, ABDA, ABMM, ACES, ACRO, ACST, ADCP, ADES, ADHI, ADMF, ADMG,
ADMR, ADRO, AGAR, AGII, AGRO, AGRS, AHAP, AISA, AKKU, AKPI, AKRA, AKSI,
ALDO, ALII, ALKA, ALMI, AMAG, AMAN, AMAR, AMFG, AMIN, AMMN, AMMS, AMOR,
AMRT, ANDI, ANJT, ANTM, APEX, APIC, APII, APLI, APLN, ARCI, AREA, ARGO,
ARII, ARKO, ARNA, ARTA, ARTO, ASDM, ASGR, ASHA, ASII, ASJT, ASLC, ASLI,
ASPI, ASPR, ASRI, ASRM, ASSA, ATAP, ATIC, ATLA, AUTO, AVIA, AWAN, AXIO,
AYAM, BABP, BABY, BACA, BACH, BAIK, BAJA, BALI, BANK, BATR, BAUT, BAYU,
BBCA, BBHI, BBKP, BBLD, BBMD, BBNI, BBRI, BBRM, BBSI, BBSS, BBTN, BBYB,
BCAP, BCIC, BDKR, BDMN, BEBS, BEEF, BEER, BEKS, BELI, BELL, BESS, BEST,
BFIN, BGTG, BHAT, BHIT, BIKE, BINA, BINO, BIPI, BIPP, BIRD, BISI, BJBR,
BJTM, BKDP, BKSL, BKSW, BLES, BLOG, BLTA, BLTZ, BLUE, BMAS, BMHS, BMRI,
BMSR, BMTR, BNBA, BNBR, BNGA, BNII, BNLI, BOAT, BOBA, BOGA, BOLA, BOLT,
BPFI, BPII, BPTR, BRAM, BREN, BRIS, BRMS, BRNA, BRPT, BSBK, BSDE, BSIM,
BSML, BSSR, BSWD, BTEK, BTON, BTPN, BTPS, BUAH, BUDI, BUKA, BUKK, BULL,
BUMI, BUVA, BVIC, BWPT, BYAN, CAKK, CAMP, CARE, CARS, CASA, CASH, CASS,
CBDK, CBPE, CBRE, CBUT, CCSI, CDIA, CEKA, CENT, CFIN, CGAS, CHEK, CHIP,
CINT, CITA, CITY, CLAY, CLEO, CLPI, CMNP, CMNT, CMPP, CMRY, CNKO, CNMA,
COAL, COCO, COIN, CPIN, CPRO, CRAB, CRSN, CSAP, CSIS, CSRA, CTBN, CTRA,
CUAN, CYBR, DAAZ, DADA, DART, DATA, DAYA, DCII, DEPO, DEWA, DEWI, DGIK,
DGNS, DGWG, DILD, DIVA, DKFT, DKHH, DLTA, DMAS, DMMX, DMND, DNAR, DNET,
DOID, DOOH, DOSS, DPUM, DRMA, DSFI, DSNG, DSSA, DUTI, DVLA, DWGL, DYAN,
EAST, ECII, EDGE, EKAD, ELIT, ELPI, ELSA, ELTY, EMAS, EMDE, EMMI, EMTK,
ENAK, ENRG, EPAC, EPMT, ERAA, ERAL, ERTX, ESSA, ESTA, ESTI, EURO, EXCL,
FAPA, FAST, FASW, FILM, FIRE, FISH, FITT, FMII, FOLK, FORE, FORU, FPNI,
FUJI, FUTR, FWCT, GDST, GDYR, GEMS, GGRM, GGRP, GHON, GIAA, GJTL, GLOB,
GLVA, GMFI, GMTD, GOLD, GOLF, GOOD, GOTO, GPRA, GPSO, GRIA, GRPM, GSMF,
GTBO, GTRA, GTSI, GULA, GUNA, GWSA, GZCO, HAIS, HAJJ, HALO, HATM, HBAT,
HDFA, HEAL, HELI, HERO, HEXA, HILL, HITS, HMSP, HOKI, HOMI, HOPE, HRME,
HRTA, HRUM, HUMI, HYGN, IATA, IBOS, IBST, ICBP, IDPR, IFII, IFSH, IGAR,
IKAI, IKBI, IKPM, IMAS, IMJS, IMPC, INAF, INCO, INDF, INDO, INDR, INDS,
INDY, INET, INKP, INOV, INPC, INPP, INPS, INRU, INTA, INTD, INTP, IOTF,
IPAC, IPCC, IPCM, IPOL, IPTV, IRRA, IRSX, ISAT, ISSP, ITIC, ITMA, ITMG,
JARR, JATI, JAWA, JECC, JECX, JELI, JGLE, JIHD, JKON, JMAS, JPFA, JRPT,
JSMR, JSPT, JTPE, KAEF, KAQI, KBAG, KBLI, KBLM, KBLV, KDSI, KDTN, KEEN,
KEJU, KETR, KIAS, KIJA, KING, KINO, KKGI, KLAS, KLBF, KMDS, KMTR, KOBX,
KOCI, KOKA, KONI, KOTA, KPIG, KRAS, KREN, KSIX, LABS, LAND, LAPD, LEAD,
LFLO, LIFE, LINK, LION, LIVE, LMPI, LPCK, LPGI, LPIN, LPKR, LPLI, LPPF,
LPPS, LSIP, LTLS, LUCY, MAHA, MAIN, MAPA, MAPB, MAPI, MARK, MASB, MAXI,
MAYA, MBAP, MBMA, MBSS, MCAS, MCOL, MCOR, MDIA, MDIY, MDKA, MDKI, MDLA,
MDLN, MDRN, MEDC, MEGA, MEJA, MERK, MFMI, MGLV, MGNA, MGRO, MHKI, MICE,
MIDI, MIKA, MINA, MINE, MKAP, MKPI, MKTR, MLBI, MLIA, MLPL, MLPT, MMIX,
MMLP, MNCN, MOLI, MORA, MPIX, MPMX, MPPA, MPRO, MPXL, MRAT, MREI, MSIN,
MSJA, MSKY, MSTI, MTDL, MTEL, MTFN, MTLA, MTMH, MTPS, MTWI, MUTU, MYOH,
MYOR, MYTX, NAIK, NASA, NATO, NAYZ, NCKL, NELY, NEST, NETV, NFCX, NICE,
NICK, NICL, NIKL, NINE, NIRO, NISP, NOBU, NPGF, NRCA, NSSS, NTBK, NZIA,
OASA, OBAT, OBMD, OKAS, OMED, OMRE, PACK, PADA, PADI, PALM, PAMG, PANI,
PANR, PANS, PART, PBID, PBRX, PBSA, PDES, PDPP, PEGE, PEHA, PEVE, PGAS,
PGEO, PGJO, PGUN, PIPA, PJAA, PJHB, PKPK, PLIN, PMJS, PMUI, PNBN, PNBS,
PNGO, PNIN, PNLF, PNSE, POLA, POLI, POLU, PORT, POWR, PPGL, PPRE, PPRO,
PRAY, PRDA, PRDL, PRIM, PSAB, PSAT, PSDN, PSGO, PSKT, PSSI, PTBA, PTMP,
PTMR, PTPP, PTPS, PTPW, PTRO, PTSN, PTSP, PUDP, PURA, PWON, PYFA, PZZA,
RAAM, RAJA, RALS, RANC, RANS, RATU, RBMS, RDTX, REAL, RELF, RELI, RGAS,
RIGS, RISE, RLCO, RMKE, RMKO, ROCK, RODA, RONY, ROTI, RSCH, SAFE, SAGE,
SAME, SAMF, SAPX, SATU, SCCO, SCMA, SCNP, SDMU, SDPC, SDRA, SFAN, SGER,
SGRO, SHID, SHIP, SIDO, SILO, SIMP, SINI, SIPD, SKBM, SKLT, SKRN, SLIS,
SMAR, SMBR, SMCB, SMDM, SMDR, SMGA, SMGR, SMIL, SMKL, SMLE, SMMA, SMMT,
SMRA, SMSM, SOCI, SOFA, SOHO, SOLA, SONA, SOSS, SOTS, SPMA, SPTO, SQMI,
SRAJ, SRSN, SRTG, SSIA, SSMS, SSTM, STAA, STAR, STRK, STTP, SULI, SUNI,
SUPA, SUPR, SURE, SURI, SWID, TALF, TAMA, TAMU, TAPG, TARA, TBIG, TBLA,
TCID, TCPI, TEBE, TFAS, TFCO, TGKA, TGUK, TIFA, TINS, TIRA, TIRT, TKIM,
TLDN, TLKM, TMAS, TMPO, TOBA, TOSK, TOTL, TOTO, TOWR, TPIA, TPMA, TRGU,
TRIM, TRIN, TRIS, TRJA, TRON, TRST, TRUE, TRUK, TRUS, TSPC, TUGU, TYRE,
UANG, UCID, UDNG, UFOE, ULTJ, UNIC, UNIQ, UNSP, UNTD, UNTR, UNVR, URBN,
UVCR, VAST, VERN, VICI, VICO, VINS, VISI, VIVA, VKTR, VOKS, VRNA, VTNY,
WAPO, WBSA, WEGE, WEHA, WGSH, WICO, WIFI, WIIM, WIKA, WINE, WINS, WIRG,
WMPP, WMUU, WOMF, WOOD, WSBP, WTON, XSPI, YELO, YOII, YPAS, YULE, YUPI,
ZATA, ZINC, ZONE, ZYRX"""
TICKERS = sorted(set(t.strip().upper() for t in IDX_TICKERS_ALL.replace("\n", ",").split(",") if t.strip()))

MULT = 3.0
MIN_TOUCH = 3
TOL_PIVOT = 0.5
MAX_ANCHOR = 8
MAX_AGE_LINE = 250
BUF_BREAK = 0.25
VAL_MIN = 1e9
SL_ATR0 = 1.0
CHAND_K = 4.0
LIMIT_PCT = 0.10
FEE_B, FEE_S = 0.0015, 0.0025
MATERAI, BATAS_MATERAI = 10_000, 10_000_000
ARB_LOCK = -0.065
RED_SCALES = [5.0, 3.0, 1.5, 0.75]
RED_AGE = {5.0: 750, 3.0: 400, 1.5: 200, 0.75: 100}
RED_BUF = 0.25
FENCE_N = 5
FENCE_IHSG = -0.01
SUSP_EXIT_N = 3


def tick(p):
    return 1 if p < 200 else 2 if p < 500 else 5 if p < 2000 else 10 if p < 5000 else 25


def floor_tick(p):
    t = tick(p)
    return np.floor(p / t + 1e-9) * t


def ceil_tick(p):
    q = floor_tick(p)
    if q < p - 1e-9:
        q = q + tick(q)
        q = floor_tick(q) if floor_tick(q) >= p - 1e-9 else q
    return float(q)


def ara_lim(p):
    return 0.35 if p < 200 else (0.25 if p <= 5000 else 0.20)


def atr_wilder(h, l, c, n=14):
    tr = np.maximum(h - l, np.maximum(abs(h - np.r_[np.nan, c[:-1]]), abs(l - np.r_[np.nan, c[:-1]])))
    tr[0] = h[0] - l[0]
    out = np.full(len(h), np.nan)
    if len(h) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(h)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def zigzag_locks(h, l, atr, mult):
    n = len(h)
    valid = np.where(~np.isnan(atr))[0]
    if len(valid) == 0:
        return [], []
    s = valid[0]
    piv, lk = [], []
    trend = 0
    hi, hi_i, lo, lo_i = h[s], s, l[s], s
    ext = ext_i = None
    for i in range(s + 1, n):
        th = mult * atr[i]
        if trend == 0:
            if h[i] > hi: hi, hi_i = h[i], i
            if l[i] < lo: lo, lo_i = l[i], i
            if lo_i < i and h[i] - lo >= th:
                piv.append((lo_i, lo, "L")); lk.append(i)
                seg = h[lo_i + 1:i + 1]; k = int(np.argmax(seg)); ext, ext_i, trend = seg[k], lo_i + 1 + k, 1
            elif hi_i < i and hi - l[i] >= th:
                piv.append((hi_i, hi, "H")); lk.append(i)
                seg = l[hi_i + 1:i + 1]; k = int(np.argmin(seg)); ext, ext_i, trend = seg[k], hi_i + 1 + k, -1
        elif trend == 1:
            if h[i] > ext: ext, ext_i = h[i], i
            elif ext - l[i] >= th:
                piv.append((ext_i, ext, "H")); lk.append(i)
                seg = l[ext_i + 1:i + 1]; k = int(np.argmin(seg)); ext, ext_i, trend = seg[k], ext_i + 1 + k, -1
        else:
            if l[i] < ext: ext, ext_i = l[i], i
            elif h[i] - ext >= th:
                piv.append((ext_i, ext, "L")); lk.append(i)
                seg = h[ext_i + 1:i + 1]; k = int(np.argmax(seg)); ext, ext_i, trend = seg[k], ext_i + 1 + k, 1
    return piv, lk


def build_line(highs, b_idx, c, atr, d):
    ib, pb = highs[b_idx]
    best = None
    for j in range(max(0, b_idx - MAX_ANCHOR), b_idx):
        ia, pa = highs[j]
        if pa <= pb or ib - ia < 10:
            continue
        slope = (pb - pa) / (ib - ia)
        touches, ok = 2, True
        for k in range(j + 1, b_idx):
            ik, pk = highs[k]
            Lk = pa + slope * (ik - ia)
            tol = TOL_PIVOT * atr[ik]
            if pk > Lk + tol:
                ok = False; break
            if abs(pk - Lk) <= tol:
                touches += 1
        if not ok or touches < MIN_TOUCH:
            continue
        t = np.arange(ia, d + 1)
        if np.any(c[ia:d + 1] > pa + slope * (t - ia) + 1e-9):
            continue
        if best is None or ia < best[0]:
            best = (ia, pa, slope, touches, ib)
    return best


def signals_for_stock(kode, df, sig_start=None):
    o, h, l, c, v = [df[x].values.astype(float) for x in ["Open", "High", "Low", "Close", "Volume"]]
    n = len(c)
    atr = atr_wilder(h, l, c)
    val20 = pd.Series(c * v).rolling(20).mean().values
    piv, lk = zigzag_locks(h, l, atr, MULT)
    lock_at = {}
    for (i, p, t), q in zip(piv, lk):
        if t == "H":
            lock_at.setdefault(q, []).append((i, p))
    highs, line, out = [], None, []
    i0 = 0 if sig_start is None else int(np.searchsorted(df.index.values, pd.Timestamp(sig_start).to_datetime64()))
    for d in range(n):
        if d in lock_at:
            for hp in lock_at[d]:
                highs.append(hp)
                nl = build_line(highs, len(highs) - 1, c, atr, d)
                if nl is not None:
                    line = nl
        if line is None:
            continue
        ia, pa, slope, touches, ib = line
        if d - ib > MAX_AGE_LINE:
            line = None; continue
        Ld = pa + slope * (d - ia)
        if c[d] >= Ld + BUF_BREAK * atr[d]:
            if d >= i0 and val20[d] >= VAL_MIN:
                out.append(dict(kode=kode, d=df.index[d], close=c[d], sl0=Ld - SL_ATR0 * atr[d], val=val20[d],
                                line=Ld, atr=atr[d], ia=ia, pa=pa, slope=slope, touches=touches))
            line = None
    return out


class _Line:
    __slots__ = ("ia", "pa", "slope", "ib", "scale")

    def __init__(s, ia, pa, ib, pb, scale):
        s.ia, s.pa, s.ib, s.scale = ia, pa, ib, scale
        s.slope = (pb - pa) / (ib - ia)

    def at(s, t):
        return s.pa + s.slope * (t - s.ia)


def _make_red(ph, k, C, ATR, d, scale):
    ib, pb = ph[k]
    best = None
    for j in range(max(0, k - 10), k):
        ia, pa = ph[j]
        if pa <= pb or ib - ia < 5:
            continue
        ln = _Line(ia, pa, ib, pb, scale)
        if not all(ph[m][1] <= ln.at(ph[m][0]) + 0.25 * ATR[ph[m][0]] for m in range(j + 1, k)):
            continue
        t = np.arange(ia, d + 1)
        if np.any(C[ia:d + 1] > ln.at(t) + 1e-12):
            continue
        if best is None or ln.at(d) < best.at(d):
            best = ln
    return best


def red_ladder(df):
    h, l, c = [df[x].values.astype(float) for x in ["High", "Low", "Close"]]
    H, L, C = np.log(h), np.log(l), np.log(c)
    n = len(C)
    ATR = atr_wilder(H, L, C)
    ev = {s: {} for s in RED_SCALES}
    for s in RED_SCALES:
        piv, lk = zigzag_locks(H, L, ATR, s)
        for (i, p, t), q in zip(piv, lk):
            if t == "H":
                ev[s].setdefault(q, []).append((i, p))
    ph = {s: [] for s in RED_SCALES}
    reds, breaks = [], []
    for d in range(n):
        if np.isnan(ATR[d]):
            continue
        for s in RED_SCALES:
            for hp in ev[s].get(d, []):
                ph[s].append(hp)
                ln = _make_red(ph[s], len(ph[s]) - 1, C, ATR, d, s)
                if ln is not None and not any(abs(r.at(d) - ln.at(d)) < 0.5 * ATR[d] for r in reds):
                    reds.append(ln)
        alive = []
        for r in reds:
            if d - r.ib > RED_AGE[r.scale]:
                continue
            lv = r.at(d)
            if C[d] >= lv + RED_BUF * ATR[d]:
                breaks.append((df.index[d], float(np.exp(lv))))
                continue
            alive.append(r)
        reds = alive
    return breaks


def prep_one(args):
    k, df = args
    s = signals_for_stock(k, df)
    rb = red_ladder(df)
    atr = atr_wilder(df.High.values.astype(float), df.Low.values.astype(float), df.Close.values.astype(float))
    return k, s, rb, atr



def trigger_price(sl):
    """Harga close tertinggi (sesuai fraksi BEI) yang sudah memicu jual: close < SL."""
    p = floor_tick(sl)
    if p >= sl - 1e-9:
        p = p - tick(p - 1e-9)
    return float(p)


# ================================================================ DATA
def _download_batch(tickers, start, end, batch=100, pause=3):
    import yfinance as yf
    out = {}
    for i in range(0, len(tickers), batch):
        grp = [f"{t}.JK" for t in tickers[i:i + batch]]
        d = None
        for _ in range(4):
            try:
                d = yf.download(grp, start=start, end=end, progress=False, auto_adjust=False, group_by="ticker", threads=True)
                break
            except Exception:
                time.sleep(10)
        if d is None or d.empty:
            continue
        lvl0 = d.columns.get_level_values(0) if isinstance(d.columns, pd.MultiIndex) else []
        for g in grp:
            if g in lvl0:
                x = d[g][["Open", "High", "Low", "Close", "Volume"]].dropna()
                x = x[(x.Close > 0) & (x.High > 0)]
                if len(x) > 250:
                    out[g[:-3]] = x
        time.sleep(pause)
    return out


def download_all(tickers=None, start=START_DATA, retries=2):
    tickers = tickers or TICKERS
    end = (pd.Timestamp.now(tz="Asia/Jakarta").normalize() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    data = _download_batch(tickers, start, end)
    for _ in range(retries):
        if not data:
            break
        D = max(df.index[-1] for df in data.values())
        lag = [k for k, df in data.items() if df.index[-1] < D and df.Volume.tail(5).sum() > 0]
        lag += [t for t in tickers if t not in data]
        if not lag:
            break
        time.sleep(20)
        again = _download_batch(lag, start, end, batch=50, pause=5)
        for k, df in again.items():
            if k not in data or df.index[-1] > data[k].index[-1]:
                data[k] = df
    return data


def fetch_ihsg(start=START_DATA):
    import yfinance as yf
    end = (pd.Timestamp.now(tz="Asia/Jakarta").normalize() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    d = yf.download("^JKSE", start=start, end=end, progress=False, auto_adjust=False)
    c = d["Close"]
    if isinstance(c, pd.DataFrame):
        c = c.iloc[:, 0]
    return c.dropna()


def clean_stock(df):
    """Bar rusak satu hari diganti bar sebelumnya; split yang tidak disesuaikan dikoreksi."""
    df = df.copy().astype(float)
    for _ in range(5):
        c = df.Close.values
        changed = False
        for t in range(1, len(c)):
            if c[t - 1] < 10:
                continue
            r = c[t] / c[t - 1] - 1
            if abs(r) <= 0.36:
                continue
            nxt = c[t + 1] / c[t] - 1 if t + 1 < len(c) else 0
            if t + 1 < len(c) and abs(nxt) > 0.36 and np.sign(nxt) != np.sign(r):
                for col in ["Open", "High", "Low", "Close"]:
                    df.iloc[t, df.columns.get_loc(col)] = c[t - 1]
                df.iloc[t, df.columns.get_loc("Volume")] = 0
            else:
                ratio = c[t] / c[t - 1]
                for col in ["Open", "High", "Low", "Close"]:
                    df.iloc[:t, df.columns.get_loc(col)] *= ratio
                df.iloc[:t, df.columns.get_loc("Volume")] /= ratio
            changed = True
            break
        if not changed:
            break
    return df


def prepare(data, procs=None):
    """Sinyal v1.2, tembus tangga merah, ATR untuk semua saham."""
    items = list(data.items())
    try:
        from multiprocessing import Pool
        with Pool(procs or max(1, os.cpu_count() or 1)) as pool:
            R = pool.map(prep_one, items, chunksize=8)
    except Exception:
        R = [prep_one(x) for x in items]
    P = {"ATRS": {}}
    rb_by, sig_by_day = {}, {}
    for k, s, rb, atr in R:
        P["ATRS"][k] = pd.Series(atr, index=data[k].index)
        rb_by[k] = pd.DataFrame(rb, columns=["d", "lv"]).set_index("d")["lv"] if rb else pd.Series(dtype=float)
        for x in s:
            sig_by_day.setdefault(x["d"], []).append(x)
    return P, rb_by, sig_by_day


def calendar(data):
    return sorted(set().union(*[set(df.index) for df in data.values()]))


def set_ihsg(ihsg, cal):
    global IHSG_RET
    IHSG_RET = ihsg.reindex(cal).ffill().pct_change()
    return IHSG_RET


# ================================================================ KALENDER BURSA
def is_bursa(d):
    d = pd.Timestamp(d)
    return d.weekday() < 5 and str(d.date()) not in LIBUR


def next_bursa(d, n=1, cal=None):
    d = pd.Timestamp(d)
    if cal is not None:
        nxt = [x for x in cal if x > d]
        if len(nxt) >= n:
            return nxt[n - 1]
    x = d
    while n > 0:
        x += pd.Timedelta(days=1)
        if is_bursa(x):
            n -= 1
    return x


# ================================================================ STATE
def new_state(modal):
    return dict(versi=VERSION, akun=AKUN, modal_awal=float(modal), cash=float(modal), reserved=0.0, pos={}, pend_buy={},
                carry={}, log=[], skipped=[], events=[], materai_total=0.0, equity=[], need=0.0, need_hist=[],
                tgt_hist=[], target=0.0, pend_dep=[], setor=0.0, tarik=0.0, idle_run=0, last_date=None,
                start_date=None, ihsg_start=None, last_report_sl={})


def _ev(st, d, **kw):
    st["events"].append(dict(d=str(pd.Timestamp(d).date()), **kw))


# ================================================================ SATU HARI BURSA (aturan R2)
def step(st, d, data, P, rb_by, sig_by_day):
    """Pagi: jual & beli market order di open. Sore: cek SL, naikkan SL, pagar jual.
    Malam: sinyal baru (didahulukan) lalu tambahan untuk saham yang SL-nya naik hari ini."""
    ds = str(d.date())
    cash_in_next = 0.0
    trx_val = 0.0
    pos, pend, carry = st["pos"], st["pend_buy"], st["carry"]
    # ---- PAGI: suspensi ke-3 dibuka -> jual
    if SUSP_EXIT_N:
        for k, p in pos.items():
            df = data.get(k)
            if p["sell"] or df is None or d not in df.index or p.get("zrun", 0) < 1 or p.get("neps", 0) < SUSP_EXIT_N:
                continue
            if float(df.at[d, "Volume"]) > 0:
                p["sell"] = True; p["flag_d"] = ds; p["src"] = "suspensi dibuka"
    # ---- PAGI: jual market order di open
    for k in list(pos):
        p = pos[k]
        if not p["sell"]:
            continue
        df = data.get(k)
        if df is None or d not in df.index:
            continue
        i = df.index.get_loc(d)
        b = df.iloc[i]
        pc = df.Close.iloc[i - 1] if i > 0 else b.Close
        if b.Volume <= 0 or (b.High == b.Low and b.Close / pc - 1 <= ARB_LOCK):
            _ev(st, d, jenis="JUAL TERTUNDA", kode=k, alasan="suspensi" if b.Volume <= 0 else "ARB terkunci")
            continue
        px = float(b.Open)
        val = p["lot"] * 100 * px
        net = val * (1 - FEE_S)
        trx_val += val
        cash_in_next += net
        st["log"].append(dict(kode=k, sig=p["sig_d"], beli=p["ed"], jual=ds, lot=p["lot"], harga_beli=p["ent"],
                              harga_jual=px, modal=p["cost"], hasil=net, pnl=net - p["cost"], ret=net / p["cost"] - 1,
                              nfill=p.get("nfill", 1)))
        _ev(st, d, jenis="JUAL", kode=k, lot=p["lot"], harga=px, pnl=net - p["cost"], ret=net / p["cost"] - 1)
        del pos[k]
    # ---- PAGI: beli market order di open
    for k in list(pend):
        o = pend.pop(k)
        df = data.get(k)
        st["reserved"] -= o["reserve"]; st["cash"] += o["reserve"]
        if o["add"] and k not in pos:
            continue
        filled, why = False, "tidak ada data"
        if df is not None and d in df.index:
            b = df.loc[d]
            pcl = float(df.Close.iloc[df.index.get_loc(d) - 1]) if df.index.get_loc(d) > 0 else float(b.Open)
            ara_lock = b.Open >= b.High and b.Open / pcl - 1 >= ara_lim(pcl) - 0.01
            if b.Volume > 0 and not ara_lock:
                px, filled = float(b.Open), True
            else:
                why = "ARA terkunci" if b.Volume > 0 else "suspensi"
        if filled:
            lot = o["lot"]; cost = lot * 100 * px * (1 + FEE_B)
            if cost > st["cash"]:
                filled, why = False, "kas kurang saat isi"
        if not filled:
            carry[k] = o
            _ev(st, d, jenis="TIDAK TERISI", kode=k, lot=o["lot"], alasan=why, add=o["add"])
            continue
        st["cash"] -= cost; trx_val += lot * 100 * px
        if k in pos:
            p = pos[k]
            p["ent"] = (p["ent"] * p["lot"] + px * lot) / (p["lot"] + lot)
            p["lot"] += lot; p["cost"] += cost; p["nfill"] += 1
            _ev(st, d, jenis="TAMBAH", kode=k, lot=lot, harga=px, ke=p["nfill"])
        else:
            s = o["s"]
            pos[k] = dict(ed=ds, ent=px, lot=lot, cost=cost, sl0=o["sl0"], sl=o["sl0"], steps=0, csteps=0, hh=0.0,
                          sig_d=o["d"], sell=False, src="garis-1ATR", nfill=1, ia=s["ia"], pa=s["pa"], slope=s["slope"])
            _ev(st, d, jenis="BELI", kode=k, lot=lot, harga=px)
    # ---- SORE: catatan suspensi
    for k, p in pos.items():
        df = data.get(k)
        if df is None or d not in df.index or pd.Timestamp(p["ed"]) >= d:
            continue
        if float(df.at[d, "Volume"]) <= 0:
            if p.get("zrun", 0) == 0:
                p["neps"] = p.get("neps", 0) + 1
            p["zrun"] = p.get("zrun", 0) + 1
        else:
            p["zrun"] = 0
    # ---- SORE: cek SL lalu naikkan SL
    for k, p in pos.items():
        df = data.get(k)
        if df is None or d not in df.index or p["sell"]:
            continue
        c = float(df.at[d, "Close"])
        if c < p["sl"]:
            p["sell"] = True; p["flag_d"] = ds; p["src_jual"] = "close < SL"
            continue
        _raise_sl(p, k, d, df, P, rb_by)
    # ---- SORE: pagar jual
    if FENCE_N and IHSG_RET is not None and d in IHSG_RET.index and IHSG_RET.at[d] <= FENCE_IHSG:
        baru = [(k, p) for k, p in pos.items() if p["sell"] and p.get("flag_d") == ds and not p.get("delayed")]
        if len(baru) >= FENCE_N:
            for k, p in baru:
                p["sell"] = False; p["delayed"] = True; p["delay_d"] = ds
                _raise_sl(p, k, d, data[k], P, rb_by)
                _ev(st, d, jenis="TUNDA JUAL", kode=k, n=len(baru), ihsg=float(IHSG_RET.at[d]))
    if trx_val > BATAS_MATERAI:
        st["cash"] -= MATERAI; st["materai_total"] += MATERAI
    st["cash"] += cash_in_next

    # ---- MALAM: order besok
    def close_of(k):
        df = data[k]
        return float(df.Close[df.index <= d].iloc[-1])

    def order(k, c, add, s=None, sl0=None, d0=None, ulang=False):
        amt = LAPIS if add else FIRST
        used = pos[k]["cost"] if (add and k in pos) else 0.0
        amt = min(amt, CAP - used)
        lot = max(1, int(amt // (c * 100 * (1 + FEE_B))))
        if used + lot * 100 * c * (1 + FEE_B) > CAP + 1:
            if not add:
                st["skipped"].append((ds, k, "1 lot > batas per saham"))
            return
        reserve = lot * 100 * float(floor_tick(c * (1 + ara_lim(c)))) * (1 + FEE_B)
        st["need"] = st.get("need", 0.0) + reserve
        if reserve > st["cash"]:
            st["skipped"].append((ds, k, "kas kurang" if not add else "kas kurang (tambah)")); return
        st["cash"] -= reserve; st["reserved"] += reserve
        pend[k] = dict(d=d0 or ds, close=c, lim=c, lot=lot, reserve=reserve, add=add, s=s, sl0=sl0, ulang=ulang)

    for k in list(carry):
        o = carry.pop(k)
        c = close_of(k)
        if o["add"]:
            if k not in pos or pos[k]["sell"]:
                continue
        else:
            if k in pos or c < o["sl0"]:
                continue
        order(k, c, o["add"], o["s"], o["sl0"], o["d"], ulang=True)
    for s in sorted(sig_by_day.get(d, []), key=lambda z: -z["val"]):
        k = s["kode"]
        if k in pos or k in pend:
            st["skipped"].append((ds, k, "sudah dipegang")); continue
        order(k, float(s["close"]), False, dict(ia=int(s["ia"]), pa=float(s["pa"]), slope=float(s["slope"])),
              float(s["sl0"]))
    for k, p in list(pos.items()):
        if p["sell"] or k in pend:
            continue
        if d not in data[k].index:
            continue
        if p.get("up") == ds:
            order(k, float(data[k].at[d, "Close"]), True)
    # ---- nilai akun
    mv = 0.0
    for k, p in pos.items():
        mv += p["lot"] * 100 * close_of(k)
    st["equity"].append(dict(d=ds, cash=st["cash"], reserved=st["reserved"], mv=mv, eq=st["cash"] + st["reserved"] + mv,
                             npos=len(pos), cost=sum(p["cost"] for p in pos.values()), dep=0.0))
    st["events"] = st["events"][-400:]
    if st["cash"] < -1e-6:
        raise RuntimeError(f"Kas negatif di {d}: {st['cash']}")
    return st


def _raise_sl(p, k, d, df, P, rb_by):
    rb = rb_by.get(k)
    if rb is not None and d in rb.index and d > pd.Timestamp(p["sig_d"]):
        lv = float(rb.loc[[d]].max())
        if lv > p["sl"]:
            p["sl"] = lv; p["steps"] += 1; p["src"] = "merah tembus"; p["up"] = str(d.date())
    p["hh"] = max(p["hh"], float(df.at[d, "High"]))
    ch = p["hh"] - CHAND_K * float(P["ATRS"][k].at[d])
    if ch > p["sl"]:
        p["sl"] = ch; p["csteps"] += 1; p["src"] = "high-4ATR"; p["up"] = str(d.date())


def day(st, d, data, P, rb_by, sig_by_day, cal=None, deposit=True):
    """Satu hari bursa lengkap: setoran masuk, aturan R2, lalu peringatan kas (setor/tarik)."""
    ds = str(d.date())
    dep_in = 0.0
    for x in [x for x in st["pend_dep"] if x["tiba"] <= ds]:
        st["cash"] += x["rp"]; st["setor"] += x["rp"]; dep_in += x["rp"]
        _ev(st, d, jenis="SETOR MASUK", rp=x["rp"])
    st["pend_dep"] = [x for x in st["pend_dep"] if x["tiba"] > ds]
    st["need"] = 0.0
    step(st, d, data, P, rb_by, sig_by_day)
    # ---- peringatan kas: perkiraan 3 hari = 3 x p90 kebutuhan order harian 60 hari
    st["need_hist"] = (st["need_hist"] + [st["need"]])[-HPROJ:]
    target = LEAD * float(np.percentile(st["need_hist"], Q))
    st["target"] = target
    cash = st["cash"]
    eq = st["equity"][-1]["eq"]
    tarik_amt = 0.0
    if deposit:
        gap = target - cash - sum(x["rp"] for x in st["pend_dep"])
        if gap > 0:
            tiba = next_bursa(d, LEAD, cal)
            st["pend_dep"].append(dict(d=ds, rp=gap, tiba=str(tiba.date())))
            _ev(st, d, jenis="PERINGATAN SETOR", rp=gap, tiba=str(tiba.date()))
    idle = cash / eq if eq > 0 else 0
    st["idle_run"] = st["idle_run"] + 1 if idle > IDLE_W else 0
    st["tgt_hist"] = (st["tgt_hist"] + [target])[-FLOOR_LB:]
    if st["idle_run"] >= IDLE_DAYS and not st["pend_dep"]:
        floor = max(st["tgt_hist"])
        amt = min(cash - floor, st["setor"] - st["tarik"])
        if amt > TARIK_MIN:
            st["cash"] -= amt; st["tarik"] += amt; st["idle_run"] = 0; tarik_amt = amt
            st["equity"][-1]["eq"] -= amt; st["equity"][-1]["cash"] -= amt
            _ev(st, d, jenis="TARIK", rp=amt)
    st["equity"][-1]["dep"] = dep_in - tarik_amt
    st["equity"][-1]["setor"] = st["setor"]; st["equity"][-1]["tarik"] = st["tarik"]
    st["last_date"] = ds
    return st


def backtest(data, P, rb_by, sig_by_day, start="2020-01-01", end=None, modal=100e6, deposit=True):
    cal = calendar(data)
    st = new_state(modal)
    days = [d for d in cal if d >= pd.Timestamp(start) and (end is None or d <= pd.Timestamp(end))]
    for d in days:
        day(st, d, data, P, rb_by, sig_by_day, cal, deposit)
    return st


def init_live(data, P, rb_by, sig_by_day, ihsg, start_day, modal):
    """State live baru. Riwayat kebutuhan order (untuk peringatan kas) diambil dari backtest R2
    100 jt mulai 2020 sampai hari bursa sebelum start_day; lalu start_day diproses dengan modal live."""
    D = pd.Timestamp(start_day)
    bt = backtest(data, P, rb_by, sig_by_day, "2020-01-01", D - pd.Timedelta(days=1), 100e6, True)
    st = new_state(modal)
    st["need_hist"] = bt["need_hist"][-HPROJ:]
    st["tgt_hist"] = bt["tgt_hist"][-FLOOR_LB:]
    day(st, D, data, P, rb_by, sig_by_day)
    st["start_date"] = str(D.date())
    st["ihsg_start"] = float(ihsg[ihsg.index <= D].iloc[-1])
    st["ihsg_hist"] = {str(D.date()): st["ihsg_start"]}
    return st


# ================================================================ LAPORAN
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BLN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tgl(d, hari=True, singkat=False):
    d = pd.Timestamp(d)
    h = HARI[d.weekday()][:3] if singkat else HARI[d.weekday()]
    return (f"{h} " if hari else "") + f"{d.day} {BLN[d.month - 1]} {d.year}"


def rp(x):
    return ("−" if x < -0.5 else "") + "Rp" + f"{abs(x):,.0f}".replace(",", ".")


def num(x):
    return f"{x:,.0f}".replace(",", ".")


def jt(x):
    return f"{x / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " jt"


def pct(x):
    return f"{x * 100:+.1f}%".replace(".", ",")


def twr(st):
    prod, prev = 1.0, None
    for e in st["equity"]:
        if e["d"] < st["start_date"]:
            continue
        if prev is None:
            base = st["modal_awal"]
        else:
            base = prev
        prod *= (e["eq"] - e.get("dep", 0.0)) / base if base > 0 else 1.0
        prev = e["eq"]
    return prod - 1


def _close(data, k, D):
    df = data[k]
    return float(df.Close[df.index <= D].iloc[-1])


def order_rows(st, data, D):
    """Baris tabel aksi hari bursa berikutnya."""
    rows = []
    for k, p in st["pos"].items():
        if p["sell"]:
            c = _close(data, k, D)
            pl = c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1
            why = "suspensi ke-%d dibuka" % p.get("neps", 0) if p.get("src") == "suspensi dibuka" else f"kena SL (close ≤ {num(trigger_price(p['sl']))})"
            rows.append(("JUAL", f"{k} ({why}, {pct(pl)})", num(p["lot"]), num(c), "–", "–"))
    if not any(r[0] == "JUAL" for r in rows):
        rows.append(("JUAL", "–", "–", "–", "–", "–"))
    nb = 0
    for k, o in st["pend_buy"].items():
        if o["add"]:
            p = st["pos"][k]
            ket = f"{k} (tambah ke-{p['nfill'] + 1}, SL naik" + (", ulang" if o.get("ulang") else "") + ")"
            sl = trigger_price(p["sl"])
        else:
            ket = f"{k} (sinyal baru" + (f" {tgl(o['d'], False)}, ulang" if o.get("ulang") else "") + ")"
            sl = trigger_price(o["sl0"])
        rows.append(("BELI", ket, num(o["lot"]), num(o["close"]), num(sl), rp(o["reserve"])))
        nb += 1
    if nb == 0:
        rows.append(("BELI", "–", "–", "–", "–", "–"))
    return rows


def md_table(head, rows):
    L = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    L += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return L


def kas_rows(st, D):
    ds = str(D.date())
    baru = [x for x in st["pend_dep"] if x["d"] == ds]
    jalan = [x for x in st["pend_dep"] if x["d"] != ds]
    tarik = [e for e in st["events"] if e["d"] == ds and e["jenis"] == "TARIK"]
    R = [("Kas sistem R2 sebelum order", rp(st["cash"] + st["reserved"])),
         ("Dana dikunci order beli", rp(st["reserved"])),
         ("Sisa kas setelah order", rp(st["cash"]))]
    if jalan:
        for x in jalan:
            R.append(("Setoran dalam perjalanan", f"{rp(x['rp'])} (masuk sebelum pre-opening {tgl(x['tiba'], singkat=True)})"))
    else:
        R.append(("Setoran dalam perjalanan", "–"))
    if baru:
        x = baru[0]
        R.append(("Setor baru (peringatan kas)", f"**{rp(x['rp'])}**, masuk paling lambat sebelum pre-opening {tgl(x['tiba'], singkat=True)}"))
    else:
        R.append(("Setor baru (peringatan kas)", "tidak perlu"))
    R.append(("Tarik ke tabungan", f"**{rp(tarik[0]['rp'])}** (kas menganggur > 50% selama 20 hari bursa)" if tarik else "–"))
    R.append(("Perkiraan kebutuhan 3 hari", rp(st["target"])))
    return R


def catatan(st, data, D):
    ds = str(D.date())
    L = ["Dana dikunci memakai harga batas ARA (+35% untuk saham ≤ Rp200, +25% untuk Rp200–5.000, +20% di atas Rp5.000). "
         "Setelah terisi di harga open, sisanya kembali jadi kas.",
         "Ketik jumlah lot sesuai tabel, jangan pakai slider persen saldo.",
         "Market order berjenis FAK: lot yang tidak terisi otomatis batal. Cek lagi setelah jam 09.00."]
    lewat = [k for (d0, k, a) in st["skipped"] if d0 == ds and a == "kas kurang"]
    lewat_t = [k for (d0, k, a) in st["skipped"] if d0 == ds and a == "kas kurang (tambah)"]
    besar = [k for (d0, k, a) in st["skipped"] if d0 == ds and a == "1 lot > batas per saham"]
    if lewat:
        L.append("Sinyal baru dilewati karena kas kurang: " + ", ".join(lewat) + ".")
    if lewat_t:
        L.append("Tambahan dilewati karena kas kurang: " + ", ".join(lewat_t) + ".")
    if besar:
        L.append("Dilewati karena harga 1 lot melebihi Rp15 jt: " + ", ".join(besar) + ".")
    tunda = [e for e in st["events"] if e["d"] == ds and e["jenis"] == "TUNDA JUAL"]
    if tunda:
        L.append(f"Pagar jual aktif: {tunda[0]['n']} posisi kena SL dan IHSG {pct(tunda[0]['ihsg'])}. "
                 "Jual ditunda 1 hari: " + ", ".join(e["kode"] for e in tunda) + ". Jangan dijual besok.")
    for k, p in st["pos"].items():
        if p.get("zrun", 0) > 0 and not p["sell"]:
            L.append(f"{k} sedang suspensi ke-{p.get('neps', 0)} ({p['zrun']} hari bursa)."
                     + (" Begitu dibuka, jual market order di pre-opening hari itu." if p.get("neps", 0) >= SUSP_EXIT_N else ""))
    return L


def report(st, data, ihsg, D):
    """Kembalikan (banner, banner_pagi, teks pagi, teks malam)."""
    ds = str(D.date())
    NB = next_bursa(D)
    hk = HARI[D.weekday()]
    rows = order_rows(st, data, D)
    # ---------- PAGI
    P = [f"**R2 • {AKUN} • {tgl(NB)}**", "Market order pre-opening, pasang 08.45–08.55 (terkunci mulai 08.56)", ""]
    P += md_table(["Aksi", "Kode", "Lot", f"Close {hk}", "Jual jika close ≤", "Dana dikunci"], rows)
    P += [""] + md_table(["Kas", "Rupiah"], kas_rows(st, D))
    P += ["", "Keterangan:"] + ["- " + x for x in catatan(st, data, D)]
    P += ["", f"_Data close {tgl(D)}. Laporan mekanis: dianggap semua perintah dijalankan penuh._"]
    # ---------- MALAM
    M = [f"**R2 • {AKUN} • close {tgl(D)}**"]
    aktif = [k for k, df in data.items() if len(df) and df.index[-1] >= D - pd.Timedelta(days=10)
             and df.Volume[df.index <= D].tail(5).sum() > 0]
    lengkap = sum(1 for k in aktif if D in data[k].index)
    M.append(f"Data {lengkap}/{len(aktif)} emiten aktif ter-update" + (" ✓" if lengkap >= 0.95 * len(aktif) else " ⚠"))
    M += ["", f"**Order {tgl(NB)}** (market order pre-opening 08.45–08.55)", ""]
    M += md_table(["Aksi", "Kode", "Lot", f"Close {hk}", "Jual jika close ≤", "Dana dikunci"], rows)
    # eksekusi mekanis hari ini
    ev = [e for e in st["events"] if e["d"] == ds]
    M += ["", f"**Eksekusi mekanis {tgl(D, singkat=True)}** (dianggap ikut penuh)"]
    ex = []
    for e in ev:
        j = e["jenis"]
        if j == "BELI":
            ex.append(f"- ✓ Beli {e['kode']} {num(e['lot'])} lot @{num(e['harga'])}")
        elif j == "TAMBAH":
            ex.append(f"- ✓ Tambah {e['kode']} {num(e['lot'])} lot @{num(e['harga'])} (beli ke-{e['ke']})")
        elif j == "JUAL":
            ex.append(f"- ✓ Jual {e['kode']} {num(e['lot'])} lot @{num(e['harga'])} → {pct(e['ret'])} / {rp(e['pnl'])}")
        elif j == "TIDAK TERISI":
            ex.append(f"- ✗ {e['kode']} {num(e['lot'])} lot tidak terisi ({e['alasan']}), diulang di order besok")
        elif j == "JUAL TERTUNDA":
            ex.append(f"- ✗ Jual {e['kode']} tidak bisa ({e['alasan']}), diulang besok")
        elif j == "SETOR MASUK":
            ex.append(f"- ✓ Setoran masuk {rp(e['rp'])}")
    M += ex if ex else ["- Tidak ada transaksi."]
    # posisi
    prev = st.get("last_report_sl", {})
    full = D.weekday() == 4
    baru = {e["kode"] for e in ev if e["jenis"] in ("BELI", "TAMBAH")}
    prow, now_sl, sama = [], {}, 0
    for k, p in sorted(st["pos"].items()):
        c = _close(data, k, D)
        trig = trigger_price(p["sl"])
        now_sl[k] = trig
        naik = p.get("up") == ds
        pl = c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1
        st_ = "JUAL besok" if p["sell"] else ("SL naik ↑" if naik else ("baru" if k in baru else "hold"))
        r = (k, num(p["lot"]), num(round(p["ent"])), num(c), pct(pl), rp(p["cost"]), num(trig), st_)
        if full or naik or p["sell"] or k in baru:
            prow.append(r)
        else:
            sama += 1
    M += ["", f"**Posisi ({len(st['pos'])})**" + (" — lengkap (Jumat)" if full else " — yang berubah saja"), ""]
    if prow:
        M += md_table(["Kode", "Lot", "Avg", "Close", "P/L", "Modal", "Jual jika close ≤", "Status"], prow)
    else:
        M.append("Tidak ada perubahan." if st["pos"] else "Belum ada posisi.")
    if sama:
        M.append(f"{sama} posisi lain tidak berubah.")
    # kas
    M += [""] + md_table(["Kas", "Rupiah"], kas_rows(st, D))
    # akun
    eq = st["equity"][-1]["eq"]
    net = st["modal_awal"] + st["setor"] - st["tarik"]
    L = st["log"]
    realized = sum(x["pnl"] for x in L)
    gp = sum(x["pnl"] for x in L if x["pnl"] > 0); gl = -sum(x["pnl"] for x in L if x["pnl"] <= 0)
    ih = float(ihsg[ihsg.index <= D].iloc[-1]) if len(ihsg[ihsg.index <= D]) else None
    if ih:
        st.setdefault("ihsg_hist", {})[ds] = ih
    ih_ret = ih / st["ihsg_start"] - 1 if (ih and st.get("ihsg_start")) else None
    A = [("Ekuitas", rp(eq)), ("Modal bersih (awal + setor − tarik)", rp(net)), ("Untung bersih", rp(eq - net)),
         ("Realized", f"{rp(realized)} ({len(L)} trade, PF {f'{gp / gl:.2f}'.replace('.', ',') if gl > 0 else '–'})"),
         ("Return sistem vs IHSG", f"{pct(twr(st))} vs {pct(ih_ret) if ih_ret is not None else '–'} (sejak {tgl(st['start_date'], False)})")]
    M += [""] + md_table(["Akun", ""], A)
    M += ["", "Keterangan:"] + ["- " + x for x in catatan(st, data, D)[3:]] if len(catatan(st, data, D)) > 3 else []
    # banner
    jual = [f"{k} {num(p['lot'])}" for k, p in st["pos"].items() if p["sell"]]
    beli = [f"{k} {num(o['lot'])}" for k, o in st["pend_buy"].items() if not o["add"]]
    tamb = [f"{k} {num(o['lot'])}" for k, o in st["pend_buy"].items() if o["add"]]
    sb = [x for x in st["pend_dep"] if x["d"] == ds]
    tk = [e for e in st["events"] if e["d"] == ds and e["jenis"] == "TARIK"]
    aksi = ("Jual " + (", ".join(jual) or "-") + " · Beli " + (", ".join(beli) or "-") + " · Tambah " + (", ".join(tamb) or "-")
            + (f" · Setor {jt(sb[0]['rp'])} s.d. {tgl(sb[0]['tiba'], False)}" if sb else "")
            + (f" · Tarik {jt(tk[0]['rp'])}" if tk else ""))
    banner = f"R2 {AKUN} · {tgl(NB, singkat=True)}: " + aksi
    banner_pagi = f"Pagi R2 {AKUN} · " + aksi
    st["last_report_sl"] = now_sl
    return banner, banner_pagi, "\n".join(P), "\n".join(M), NB


def write_report(path, st, data, ihsg, D, label=""):
    banner, bp, P, M, NB = report(st, data, ihsg, D)
    open(path, "w").write(f"TANGGAL DATA: {D.date()}\nSTATUS: OK\nHARI BURSA BERIKUTNYA: {NB.date()}\n"
                          f"BANNER: {label}{banner}\nBANNER PAGI: {label}{bp}\n\n=== PAGI ===\n{label}{P}\n\n=== MALAM ===\n{label}{M}\n")
    return banner


# ================================================================ STATE JSON
def state_to_json(st):
    return json.dumps(st, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else float(o), indent=0)


def state_from_json(s):
    st = json.loads(s)
    st["skipped"] = [tuple(x) for x in st.get("skipped", [])]
    return st


# ================================================================ JALAN MALAM (dipakai jadwal otomatis)
def run_nightly(state_path, out_path, now=None, raw=None, ihsg=None, wait=300):
    now = now or datetime.now(timezone(timedelta(hours=7)))
    today = pd.Timestamp(now.date())

    def tulis(status, D, msg):
        open(out_path, "w").write(f"TANGGAL DATA: {D}\nSTATUS: {status} - {msg}\nBANNER: R2 {AKUN}: {status} - {msg}\n")
        return dict(status=status, msg=msg)

    st = state_from_json(open(state_path).read())
    if not is_bursa(today):
        return tulis("LIBUR", st["last_date"], f"{tgl(today)} libur bursa, tidak ada laporan.")
    for attempt in range(3):
        r = raw if raw is not None else download_all()
        D = max(df.index[-1] for df in r.values())
        if raw is not None or D >= today:
            break
        time.sleep(wait)
    ih = ihsg if ihsg is not None else fetch_ihsg()
    if D < today:
        return tulis("GAGAL", D.date(), f"Belum ada data close {tgl(today)} (Yahoo telat). Data terakhir {D.date()}. Posisi tidak diubah.")
    aktif = [k for k, df in r.items() if df.Volume.tail(5).sum() > 0 and df.index[-1] >= D - pd.Timedelta(days=10)]
    tertinggal = [k for k in aktif if r[k].index[-1] < D]
    if ih.index[-1] < D or len(tertinggal) > 0.10 * len(aktif):
        return tulis("GAGAL", D.date(), f"Data Yahoo belum lengkap (IHSG {ih.index[-1].date()}, {len(tertinggal)}/{len(aktif)} emiten tertinggal). Posisi tidak diubah.")
    if st["last_date"] and pd.Timestamp(st["last_date"]) >= D:
        return tulis("GAGAL", D.date(), f"Data {D.date()} sudah diproses sebelumnya. Posisi tidak diubah.")
    data = {k: clean_stock(df) for k, df in r.items()}
    P, rb_by, sig_by_day = prepare(data)
    cal = calendar(data)
    set_ihsg(ih, cal)
    days = [d for d in cal if d > pd.Timestamp(st["last_date"])]
    for d in days:
        day(st, d, data, P, rb_by, sig_by_day)
    banner = write_report(out_path, st, data, ih, pd.Timestamp(st["last_date"]))
    open(state_path, "w").write(state_to_json(st))
    return dict(status="OK", banner=banner, days=[str(x.date()) for x in days])


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sp = args[0] if len(args) > 0 else "r2_state.json"
    op = args[1] if len(args) > 1 else "r2_laporan.md"
    run_nightly(sp, op)
    print(open(op).read())
