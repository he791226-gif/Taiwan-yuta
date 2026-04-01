import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 英雄名冊 (建議後續可匯入完整的 500 檔 CSV)
NAME_MAP = {
    "1905": "華紙", "2330": "台積電", "2317": "鴻海", "2454": "聯發科",
    "2603": "長榮", "2368": "金像電", "4558": "永新-KY", "1271": "晨星"
}

# 2. 密碼鎖
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwei8888": # <--- 這裡維持你的密碼
            st.session_state.authenticated = True
            st.rerun()
else:
    st.title("🚀 台股英雄手機監控台")
    symbol_input = st.text_input("輸入股票代碼 (空白分隔多檔)", "2368 4558")
    
    if st.button("開始英雄掃描"):
        symbols = symbol_input.strip().split()
        
        for raw_symbol in symbols:
            with st.container():
                try:
                    search_symbol = f"{raw_symbol}.TW"
                    df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)
                    if df.empty:
                        search_symbol = f"{raw_symbol}.TWO"
                        df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)

                    if not df.empty:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.get_level_values(0)

                        # --- 核心數據計算 ---
                        close = df['Close'].astype(float)
                        high = df['High'].astype(float)
                        low = df['Low'].astype(float)
                        vol = df['Volume'].astype(float)
                        
                        ma20 = close.rolling(window=20).mean()
                        std20 = close.rolling(window=20).std()
                        upper = ma20 + (std20 * 2)
                        ma5_v = vol.rolling(window=5).mean()
                        
                        curr_price = float(close.iloc[-1])
                        prev_price = float(close.iloc[-2])
                        curr_vol = float(vol.iloc[-1])
                        curr_ma5v = float(ma5_v.iloc[-1])
                        change_pct = ((curr_price - prev_price) / prev_price) * 100
                        bias = ((curr_price - ma20.iloc[-1]) / ma20.iloc[-1]) * 100

                        # --- 英雄評分算法 (核心邏輯回歸) ---
                        base_score = 60
                        # 1. 價格位置加分
                        if curr_price > upper.iloc[-1]: base_score += 20  # 噴發中
                        elif curr_price > ma20.iloc[-1]: base_score += 10 # 多頭
                        else: base_score -= 15 # 弱勢
                        
                        # 2. 量能加分
                        if curr_vol > curr_ma5v * 1.5: base_score += 15 # 爆量攻擊
                        
                        # 3. 漲跌幅加分 (漲停邏輯)
                        if change_pct > 8: base_score += 10
                        elif change_pct < -8: base_score -= 20

                        final_score = min(99, max(20, base_score))

                        # --- 噴發機率判斷 ---
                        if final_score >= 85: probability = "極高"
                        elif final_score >= 70: probability = "高"
                        elif final_score >= 50: probability = "普通"
                        else: probability = "低"

                        # --- UI 呈現 ---
                        name = NAME_MAP.get(raw_symbol, raw_symbol)
                        st.markdown(f"### 🛡️ {name} ({raw_symbol})")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.write(f"現價 (今日漲跌: {change_pct:.1f}%)")
                            st.title(f"$ {curr_price:.2f}")
                            st.write("攻擊力點數")
                            # 根據分數變換顏色
                            score_color = "#ff4b4b" if final_score > 70 else "#31333F"
                            st.markdown(f"<h1 style='color: {score_color}; font-size: 80px;'>{int(final_score)}</h1>", unsafe_allow_html=True)
                            st.write(f"明日噴發機率：**{probability}**")

                        with col2:
                            # 狀態標籤精準判斷
                            st.info(f"✅ 市場對比：{'強於大盤' if bias > 0 else '弱於大盤'}")
                            st.error(f"🔥 量能強度：{'攻擊爆量' if curr_vol > curr_ma5v * 1.5 else '量能平穩'}")
                            st.success(f"🚀 趨勢型態：{'多頭噴發' if curr_price > upper.iloc[-1] else '區間震盪'}")
                            st.warning(f"⚡ 動能指標：{'強勁拉升' if change_pct > 5 else '動能累積'}")

                        # 圖表中文化
                        df_plot = pd.DataFrame({
                            '收盤價(Close)': close,
                            '月線(MA20)': ma20,
                            '布林上軌(Upper)': upper
                        })
                        st.line_chart(df_plot.tail(60)) # 手機版顯示最近 60 天最清楚
                        st.markdown("---")
                        
                except Exception as e:
                    st.error(f"{raw_symbol} 掃描異常: {e}")
