import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 英雄名冊 (可持續擴充)
NAME_MAP = {
    "1905": "華紙", "2330": "台積電", "2317": "鴻海", "2454": "聯發科",
    "2603": "長榮", "2609": "陽明", "1271": "晨星" # 依此類推
}

# 2. 密碼鎖
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwai8888": # <--- 請在此修改
            st.session_state.authenticated = True
            st.rerun()
else:
    st.title("🚀 台股英雄手機監控台")
    symbol_input = st.text_input("輸入股票代碼 (空白分隔多檔)", "1905 2330")
    
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

                        # --- 指標計算 (攻擊力邏輯) ---
                        close = df['Close']
                        ma20 = close.rolling(window=20).mean()
                        std20 = close.rolling(window=20).std()
                        upper = ma20 + (std20 * 2)
                        volume = df['Volume']
                        ma_v = volume.rolling(window=5).mean() # 5日均量
                        
                        last_c = float(close.iloc[-1])
                        last_v = float(volume.iloc[-1])
                        last_mv = float(ma_v.iloc[-1])
                        bias = ((last_c - ma20.iloc[-1]) / ma20.iloc[-1]) * 100
                        
                        # --- 核心 UI 佈局 (模擬電腦版) ---
                        name = NAME_MAP.get(raw_symbol, raw_symbol)
                        st.markdown(f"### 🛡️ {name} ({raw_symbol})")
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.write("現價：")
                            st.title(f"$ {last_c:.2f}")
                            # 模擬攻擊力點數 (根據乖離與量能計算)
                            score = 60 + (10 if last_c > ma20.iloc[-1] else -20) + (20 if last_v > last_mv else 0)
                            score = min(95, max(40, score)) # 限制區間
                            st.write("攻擊力點數")
                            st.markdown(f"<h1 style='color: #ff4b4b; font-size: 80px;'>{int(score)}</h1>", unsafe_allow_html=True)
                            st.caption("明日噴發機率：計算中...")

                        with col2:
                            # 狀態標籤區
                            st.info(f"✅ 市場對比：{'強於大盤' if bias > 0 else '弱於大盤'}")
                            st.error(f"🔥 量能強度：{'攻擊爆量' if last_v > last_mv * 1.5 else '量能平穩'}")
                            st.success(f"🚀 趨勢型態：{'多頭噴發' if last_c > upper.iloc[-1] else '區間震盪'}")
                            st.warning(f"⚡ 動能指標：{'高檔強勢' if bias > 10 else '動能累積'}")

                        # 警告訊息
                        if bias > 15:
                            st.warning(f"⚠️ 攻擊過熱：乖離率 {bias:.1f}%，隨時可能反轉！")

                        # 中文化圖表
                        df_plot = pd.DataFrame({
                            '收盤價(Close)': close,
                            '月線(MA20)': ma20,
                            '布林上軌(Upper)': upper
                        })
                        st.line_chart(df_plot)
                        st.markdown("---")
                    else:
                        st.error(f"找不到 {raw_symbol}")
                except Exception as e:
                    st.error(f"{raw_symbol} 錯誤: {e}")
