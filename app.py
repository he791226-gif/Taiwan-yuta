import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# --- 英雄名冊：前500大常用名對照 (僅列部分示意，可自行按格式擴充) ---
NAME_MAP = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "1905": "華紙",
    "2303": "聯電", "2881": "富邦金", "2882": "國泰金", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2409": "友達", "3481": "群創"
    # 可持續在此新增： "代碼": "中文名",
}

# 2. 密碼鎖 (保持安全性)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwai8888":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
else:
    st.title("🚀 台股英雄手機監控台")
    # 支援空格分開多個代碼
    symbol_input = st.text_input("輸入股票代碼 (可用空格分開多個，例: 1905 2330)", "1905 2330")
    
    if st.button("開始英雄掃描"):
        # 拆分輸入的代碼列表
        symbols = symbol_input.strip().split()
        
        for raw_symbol in symbols:
            with st.container(): # 為每支股票建立獨立區塊
                name = NAME_MAP.get(raw_symbol, "未知股票")
                st.markdown(f"---")
                st.header(f"🛡️ 英雄診斷：{name} ({raw_symbol})")
                
                try:
                    search_symbol = f"{raw_symbol}.TW"
                    df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)
                    
                    if df.empty:
                        search_symbol = f"{raw_symbol}.TWO"
                        df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)

                    if not df.empty:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.get_level_values(0)
                        
                        # 指標計算
                        df['收盤價(Close)'] = df['Close']
                        df['月線(MA20)'] = df['Close'].rolling(window=20).mean()
                        df['布林上軌(Upper)'] = df['月線(MA20)'] + (df['Close'].rolling(window=20).std() * 2)
                        df['乖離率'] = ((df['Close'] - df['月線(MA20)']) / df['月線(MA20)']) * 100

                        # 最新狀態
                        last_c = df['收盤價(Close)'].iloc[-1]
                        last_bias = df['乖離率'].iloc[-1]
                        
                        # 顯示數據
                        c1, c2 = st.columns(2)
                        c1.metric("當前股價", f"{last_c:.2f}")
                        c2.metric("月線乖離率", f"{last_bias:.1f}%")

                        # 警告邏輯
                        if last_bias > 15:
                            st.warning(f"⚠️ 攻擊過熱：乖離率 {last_bias:.1f}%，建議分批獲利！")
                        elif last_bias > 0:
                            st.success(f"🔥 強勢攻擊：股價在月線上方穩定運行。")
                        else:
                            st.error(f"❄️ 防禦狀態：目前處於弱勢，多看少動。")

                        # 圖表中文化顯示
                        # 我們只選要顯示的中文欄位
                        chart_data = df[['收盤價(Close)', '月線(MA20)', '布林上軌(Upper)']]
                        st.line_chart(chart_data)
                        
                    else:
                        st.error(f"找不到代碼 {raw_symbol} 的資料")
                except Exception as e:
                    st.error(f"{raw_symbol} 掃描異常: {e}")
