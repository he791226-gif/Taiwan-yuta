import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import talib
from datetime import datetime

# =============================================================================
# 1. 安全授權系統 (確保只有你能使用這個網址)
# =============================================================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 英雄系統手機授權")
        # 你可以在這裡修改你的專屬密碼
        pwd = st.text_input("請輸入授權碼", type="password")
        if st.button("確認登入"):
            if pwd == "8888":  # <--- 請將 8888 改成你自己想要的密碼
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("授權碼錯誤，請重新輸入")
        return False
    return True

# =============================================================================
# 2. 在地化名稱對照表 (解決 yfinance 中文顯示重複或錯誤問題)
# =============================================================================
STOCK_MAP = {
    "1323": "永裕", "1905": "華紙", "3013": "晟銘電", "3031": "佰鴻",
    "4419": "松懋", "1452": "宏益", "4741": "泓瀚", "3042": "晶技",
    "6616": "特昇-KY", "1906": "寶隆", "4558": "興能高", "2330": "台積電",
    "2317": "鴻海", "2603": "長榮", "2640": "大車隊", "1717": "長興",
    "2239": "英利-KY", "6838": "台新藥", "6264": "富研", "3236": "千如",
    "6830": "汎銓", "8444": "綠河-KY"
}

# =============================================================================
# 3. 核心算力：逆勢英雄判斷 + 避險邏輯
# =============================================================================
def analyze_hero_power(sid, df, mkt_change):
    if df is None or len(df) < 30: return None
    
    close = df['Close'].values
    vol = df['Volume'].values
    current_price = close[-1]
    hero_score = 0
    
    # --- A. 市場對比 (逆勢英雄核心) ---
    stock_change = (close[-1] - close[-2]) / close[-2]
    if mkt_change < 0 and stock_change > 0:
        hero_score += 40
        mkt_status = ("💎 逆勢英雄", "blue")
    elif stock_change > mkt_change:
        hero_score += 20
        mkt_status = ("✅ 強於大盤", "green")
    else: mkt_status = ("☁️ 隨波逐流", "gray")

    # --- B. 攻擊量能 ---
    avg_vol = np.mean(vol[-20:-1])
    vol_ratio = vol[-1] / (avg_vol + 1)
    if vol_ratio > 2.0 and close[-1] > close[-2]:
        hero_score += 30
        vol_status = ("🔥 攻擊爆量", "red")
    elif vol_ratio > 1.2:
        hero_score += 15
        vol_status = ("📈 溫和放量", "orange")
    else: vol_status = ("💤 量縮盤整", "gray")

    # --- C. 趨勢型態與【乖離避險】 ---
    ma20 = talib.SMA(close, 20)
    # 💥 核心防線：計算月線乖離率 (Bias)
    bias20 = ((current_price - ma20[-1]) / ma20[-1]) * 100
    
    risk_msg = ""
    chart_status = ("💪 站穩月線", "green")
    
    # 避險邏輯：如果乖離過高，強制降分
    if bias20 > 10:
        hero_score -= 30
        risk_msg = f"🚨 警戒：高檔過熱 (乖離 {bias20:.1f}%)"
        chart_status = ("⚠️ 乖離過大", "red")
    elif close[-1] > ma20[-1]:
        hero_score += 10

    # 評價等級
    if hero_score >= 100: rank, color = "SSS級：爆發潛力", "red"
    elif hero_score >= 70: rank, color = "A級：具備動能", "orange"
    else: rank, color = "整理中", "gray"

    cname = STOCK_MAP.get(str(sid), "")
    return {
        'sid': sid, 'name': cname, 'price': f"{current_price:.2f}",
        'score': hero_score, 'rank': rank, 'color': color,
        'risk': risk_msg,
        'factors': [("市場對比", mkt_status), ("量能強度", vol_status), ("趨勢型態", chart_status)]
    }

# =============================================================================
# 4. Streamlit 網頁佈局 (手機優化版)
# =============================================================================
if check_password():
    st.set_page_config(page_title="台股英雄掃描", layout="centered")
    st.title("🚀 台股英雄手機監控台")
    st.caption("已整合月線乖離避險機制，防範追高風險")

    with st.sidebar:
        st.header("掃描設定")
        mode = st.radio("範圍", ["自選監控", "全市場掃描 (4位數)"])
        if mode == "自選監控":
            target_sids = st.text_input("輸入代號 (空格隔開)", "1323 1905 4419 6838 2330").split()
        else:
            # 這裡設定你想要全掃的 4 位數區間
            target_sids = [str(i) for i in range(1101, 1600)]

    if st.button("🏃 開始深度掃描"):
        with st.spinner("英雄集結中...請稍候"):
            # 獲取大盤數據
            mkt_df = yf.Ticker("^TWII").history(period="5d")
            mkt_change = (mkt_df['Close'].iloc[-1] - mkt_df['Close'].iloc[-2]) / mkt_df['Close'].iloc[-2]

            # 批次下載數據
            symbols = [f"{s}.TW" for s in target_sids] + [f"{s}.TWO" for s in target_sids]
            data = yf.download(symbols, period="1y", group_by='ticker', silent=True)

            results = []
            for sid in target_sids:
                df = None
                if f"{sid}.TW" in data and not data[f"{sid}.TW"].dropna().empty:
                    df = data[f"{sid}.TW"].dropna()
                elif f"{sid}.TWO" in data and not data[f"{sid}.TWO"].dropna().empty:
                    df = data[f"{sid}.TWO"].dropna()
                
                if df is not None:
                    res = analyze_hero_power(sid, df, mkt_change)
                    if res and res['score'] >= 50: # 過濾低分標的
                        results.append(res)

            results.sort(key=lambda x: x['score'], reverse=True)

            # 顯示結果列表
            st.success(f"掃描完成！找到 {len(results)} 檔具備動能標的")
            for r in results:
                with st.expander(f"【{r['score']}分】 {r['sid']} {r['name']} - {r['rank']}"):
                    st.header(f"${r['price']}")
                    if r['risk']:
                        st.error(r['risk'])
                    
                    c1, c2, c3 = st.columns(3)
                    for i, (label, (status, color)) in enumerate(r['factors']):
                        cols = [c1, c2, c3]
                        cols[i].write(f"**{label}**")
                        cols[i].write(f":{color}[{status}]")
                    
                    st.progress(min(max(r['score'], 0), 100) / 100)
