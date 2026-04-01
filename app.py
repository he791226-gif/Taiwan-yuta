import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 英雄名冊 (建議後續可匯入完整的 500 檔 CSV)
NAME_MAP = {
    "1905": "華紙", "2330": "台積電", "2317": "鴻海", "2454": "聯發科",
    "2603": "長榮", "2368": "金像電", "4558": "永新-KY", "1906": "達新"
}

# 2. 密碼鎖 (確保只有英雄本人能用)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwei8888":
            st.session_state.authenticated = True
            st.rerun()
else:
    st.title("🚀 台股英雄手機監控台")
    symbol_input = st.text_input("輸入股票代碼 (空白分隔多檔)", "2368 1906")
    
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
                        vol = df['Volume'].astype(float)
                        ma20 = close.rolling(window=20).mean()
                        std20 = close.rolling(window=20).std()
                        upper = ma20 + (std20 * 2)
                        ma5_v = vol.rolling(window=5).mean()
                        
                        curr_price = float(close.iloc[-1])
                        prev_price = float(close.iloc[-2])
                        curr_vol = float(vol.iloc[-1])
                        curr_ma5v = float(ma5_v.iloc[-1])
                        
                        # 漲跌判斷 (關鍵調適)
                        change_pct = ((curr_price - prev_price) / prev_price) * 100
                        is_crashing = change_pct < -5  # 跌幅超過 5%
                        is_soaring = change_pct > 5    # 漲幅超過 5%
                        is_below_ma20 = curr_price < ma20.iloc[-1]

                        # --- 英雄評分算法 (深度調適版) ---
                        score = 60
                        # 1. 趨勢定位
                        if curr_price > upper.iloc[-1] and not is_crashing: score += 25  # 真噴發
                        elif not is_below_ma20: score += 10 # 多頭支撐
                        else: score -= 30 # 破位扣大分

                        # 2. 量能方向 (修正爆量誤判)
                        if curr_vol > curr_ma5v * 1.5:
                            if is_crashing: score -= 20 # 逃命爆量
                            elif is_soaring: score += 15 # 攻擊爆量
                        
                        # 3. 漲跌連動
                        if change_pct < -8: score -= 20 # 跌停懲罰
                        elif change_pct > 8: score += 10 # 漲停獎勵

                        final_score = min(99, max(5, score))

                        # --- UI 呈現 ---
                        name = NAME_MAP.get(raw_symbol, raw_symbol)
                        st.markdown(f"### 🛡️ {name} ({raw_symbol})")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.write(f"現價 (今日漲跌: {change_pct:.1f}%)")
                            st.title(f"$ {curr_price:.2f}")
                            st.write("攻擊力點數")
                            # 顏色動態變化
                            color = "#ff4b4b" if final_score > 70 else ("#00cc00" if final_score < 40 else "#31333F")
                            st.markdown(f"<h1 style='color: {color}; font-size: 80px;'>{int(final_score)}</h1>", unsafe_allow_html=True)
                            
                            prob = "極低" if final_score < 30 else ("普通" if final_score < 70 else "極高")
                            st.write(f"明日噴發機率：**{prob}**")

                        with col2:
                            # 標籤狀態調適
                            if is_below_ma20:
                                st.error("❌ 市場對比：弱於大盤 (破線)")
                            else:
                                st.success("✅ 市場對比：強於大盤")

                            if curr_vol > curr_ma5v * 1.5:
                                st.markdown(f"<div style='background-color:{'#ffcccc' if is_crashing else '#ffe6e6'}; padding:10px; border-radius:5px;'>{'🆘 逃命爆量' if is_crashing else '🔥 攻擊爆量'}</div>", unsafe_allow_html=True)
                            else:
                                st.info("💎 量能強度：縮量整理")

                            if is_crashing:
                                st.error("💀 趨勢型態：空頭反轉")
                            else:
                                st.warning(f"🚀 趨勢型態：{'強烈噴發' if curr_price > upper.iloc[-1] else '多頭整理'}")

                            st.info(f"⚡ 動能指標：{'動能潰散' if is_crashing else '持續加溫'}")

                        # 圖表中文化
                        df_plot = pd.DataFrame({
                            '收盤價(Close)': close,
                            '月線(MA20)': ma20,
                            '布林上軌(Upper)': upper
                        }).tail(60)
                        st.line_chart(df_plot)
                        st.markdown("---")
                except Exception as e:
                    st.error(f"{raw_symbol} 異常: {e}")
