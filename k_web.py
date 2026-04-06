import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import talib
from datetime import datetime

# =============================================================================
# 1. 安全設定與登入檢查
# =============================================================================
def check_password():
    """簡單的密碼檢查，保護你的私密策略"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 英雄系統授權")
        pwd = st.text_input("請輸入專屬授權碼", type="password")
        if st.button("登入"):
            if pwd == "yuwei8888": # <--- 在這裡設定你的密碼
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("授權碼錯誤")
        return False
    return True

# =============================================================================
# 2. 本地字典與核心算力 (新增避險邏輯)
# =============================================================================
STOCK_MAP = {
    "1323": "永裕", "1905": "華紙", "3013": "晟銘電", "3031": "佰鴻",
    "4419": "松懋", "1452": "宏益", "4741": "泓瀚", "3042": "晶技",
    "6616": "特昇-KY", "1906": "寶隆", "4558": "興能高", "2330": "台積電"
}

def analyze_stock(sid, df, mkt_change):
    if df is None or len(df) < 30: return None
    close = df['Close'].values
    vol = df['Volume'].values
    current_price = close[-1]
    
    score = 0
    # A. 市場對比
    stock_change = (close[-1] - close[-2]) / close[-2]
    mkt_status = "✅ 強於大盤" if stock_change > mkt_change else "☁️ 隨波逐流"
    if mkt_change < 0 and stock_change > 0:
        score += 40
        mkt_status = "💎 逆勢英雄"
    elif stock_change > mkt_change: score += 20

    # B. 量能強度
    avg_vol = np.mean(vol[-20:-1])
    vol_ratio = vol[-1] / (avg_vol + 1)
    vol_status = "💤 量縮"
    if vol_ratio > 2.0 and close[-1] > close[-2]:
        score += 30
        vol_status = "🔥 攻擊爆量"
    elif vol_ratio > 1.2:
        score += 15
        vol_status = "📈 溫和放量"

    # C. 趨勢型態 + 避險邏輯 (Bias)
    ma20 = talib.SMA(close, 20)
    bias20 = ((current_price - ma20[-1]) / ma20[-1]) * 100
    
    chart_status = "💪 站穩月線"
    if close[-1] > ma20[-1]: score += 10
    
    # 💥 華紙教訓：高檔乖離過大強制扣分
    risk_msg = ""
    if bias20 > 10:
        score -= 30
        risk_msg = f"⚠️ 警告：乖離率 {bias20:.1f}% 過高，慎防回檔！"
        chart_status = "🚨 高檔過熱"

    # 評級判斷
    if score >= 100: rank, color = "SSS級：爆發潛力", "#d63031"
    elif score >= 70: rank, color = "A級：具備動能", "#e17055"
    else: rank, color = "整理中", "#636e72"

    cname = STOCK_MAP.get(str(sid), "")
    return {
        "sid": sid, "name": cname, "price": f"{current_price:.2f}",
        "score": score, "rank": rank, "color": color,
        "mkt": mkt_status, "vol": vol_status, "chart": chart_status, "risk": risk_msg
    }

# =============================================================================
# 3. 網頁介面佈局 (手機優化)
# =============================================================================
if check_password():
    st.set_page_config(page_title="台股英雄監控台", layout="wide")
    st.title("🚀 台股英雄監控台 (避險優化版)")
    
    # 側邊欄設定
    with st.sidebar:
        st.header("掃描設定")
        scan_mode = st.radio("掃描範圍", ["自選清單", "全台股 (4位數)"])
        if scan_mode == "自選清單":
            target_input = st.text_area("輸入代碼 (空白分隔)", "1323 1905 4419 2330")
            sids = target_input.split()
        else:
            sids = [str(i) for i in range(1101, 1500)] # 範例區間
            
    if st.button("🔥 開始執行深度掃描"):
        with st.spinner("英雄集結中..."):
            # 獲取大盤
            mkt_df = yf.Ticker("^TWII").history(period="5d")
            mkt_change = (mkt_df['Close'].iloc[-1] - mkt_df['Close'].iloc[-2]) / mkt_df['Close'].iloc[-2]
            
            # 批次下載
            symbols = [f"{s}.TW" for s in sids] + [f"{s}.TWO" for s in sids]
            data = yf.download(symbols, period="1y", group_by='ticker', silent=True)
            
            results = []
            for sid in sids:
                df = None
                if f"{sid}.TW" in data and not data[f"{sid}.TW"].dropna().empty:
                    df = data[f"{sid}.TW"].dropna()
                elif f"{sid}.TWO" in data and not data[f"{sid}.TWO"].dropna().empty:
                    df = data[f"{sid}.TWO"].dropna()
                
                if df is not None:
                    res = analyze_stock(sid, df, mkt_change)
                    if res and res['score'] >= 50: results.append(res)
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # 顯示結果
            if not results:
                st.warning("目前市場無符合動能之標的。")
            else:
                for r in results[:15]: # 手機版顯示前15強即可
                    with st.expander(f"【{r['score']}分】{r['sid']} {r['name']} - {r['rank']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("現價", r['price'])
                            st.write(f"**市場對比：** {r['mkt']}")
                            st.write(f"**量能強度：** {r['vol']}")
                        with col2:
                            st.write(f"**趨勢狀態：** {r['chart']}")
                            if r['risk']:
                                st.error(r['risk'])
                            else:
                                st.success("✅ 目前位階安全")
                        st.progress(min(max(r['score'], 0), 100) / 100)
