import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 2. 密碼鎖
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 英雄系統手機授權")
        pwd = st.text_input("輸入授權密碼", type="password")
        if st.button("登入"):
            if pwd == "yuwai8888": # <--- 記得改密碼
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密碼錯誤")
        return False
    return True

if check_password():
    st.title("🚀 台股英雄手機監控台")
    symbol_input = st.text_input("輸入股票代碼 (例: 1905, 2330)", "1905")
    
    if st.button("開始英雄掃描"):
        with st.spinner("正在注入英雄能量..."):
            try:
                raw_symbol = symbol_input.strip().split()[0]
                search_symbol = f"{raw_symbol}.TW" if not ("." in raw_symbol) else raw_symbol
                df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)
                
                if df.empty and ".TW" in search_symbol:
                    search_symbol = search_symbol.replace(".TW", ".TWO")
                    df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)

                if not df.empty:
                    # 關鍵修正：解決 MultiIndex 報錯問題
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    close = df['Close']
                    high = df['High']
                    low = df['Low']

                    # --- 英雄指標計算區 ---
                    # 1. 月線 & 布林
                    df['MA20'] = close.rolling(window=20).mean()
                    df['STD20'] = close.rolling(window=20).std()
                    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
                    
                    # 2. 月線乖離率 (攻擊力指標)
                    df['Bias'] = ((close - df['MA20']) / df['MA20']) * 100
                    
                    # 3. RSI 計算 (強弱)
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))

                    # 4. KD 指標 (手寫邏輯)
                    low_min = low.rolling(window=9).min()
                    high_max = high.rolling(window=9).max()
                    rsv = (close - low_min) / (high_max - low_min) * 100
                    df['K'] = rsv.ewm(com=2).mean()
                    df['D'] = df['K'].ewm(com=2).mean()

                    # 取得最新值
                    last_c = float(close.iloc[-1])
                    last_bias = float(df['Bias'].iloc[-1])
                    last_k = float(df['K'].iloc[-1])
                    last_rsi = float(df['RSI'].iloc[-1])
                    
                    # 數據面板
                    st.success(f"英雄掃描完成！")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("當前股價", f"{last_c:.2f}")
                    c2.metric("月線乖離", f"{last_bias:.1f}%")
                    c3.metric("K值 (轉折)", f"{last_k:.1f}")
                    c4.metric("RSI (強弱)", f"{last_rsi:.1f}")

                    # --- 攻擊力判斷 ---
                    st.subheader("🛡️ 英雄攻擊力診斷")
                    if last_bias > 10:
                        st.warning(f"⚠️ **攻擊過熱**：乖離率已達 {last_bias:.1f}%，隨時可能反轉！")
                    elif last_bias > 0:
                        st.info(f"🔥 **攻擊發動**：股價站在月線之上，動能增強中。")
                    else:
                        st.error(f"❄️ **能量不足**：目前在月線下方，建議防禦。")

                    # 圖表顯示
                    st.line_chart(df[['Close', 'MA20', 'Upper']])
                    
                else:
                    st.error("找不到資料")
            except Exception as e:
                st.error(f"系統異常: {e}")
