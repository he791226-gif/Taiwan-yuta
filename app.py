import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 2. 簡單密碼鎖
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 英雄系統手機授權")
        pwd = st.text_input("輸入授權密碼", type="password")
        if st.button("登入"):
            if pwd == "yuwai8888":  # <--- 這裡請記得改成你的密碼
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密碼錯誤")
        return False
    return True

if check_password():
    st.title("🚀 台股英雄手機監控台")
    st.markdown("---")
    
    # 修改提示：請用戶一次輸入一個代碼
    symbol_input = st.text_input("輸入單一股票代碼 (例: 1905 或 2330)", "1905")
    
    if st.button("開始英雄掃描"):
        with st.spinner("正在抓取數據..."):
            try:
                # 處理輸入，確保只取第一個代碼並自動補後綴
                raw_symbol = symbol_input.strip().split()[0] 
                if not (raw_symbol.endswith(".TW") or raw_symbol.endswith(".TWO")):
                    search_symbol = f"{raw_symbol}.TW"
                else:
                    search_symbol = raw_symbol

                # 抓取資料，強制使用 group_by='column' 確保格式正確
                df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)
                
                # 如果上市找不到，試試上櫃
                if df.empty and ".TW" in search_symbol:
                    search_symbol = f"{raw_symbol}.TWO"
                    df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)

                if not df.empty:
                    # 關鍵修正：確保我們只取 'Close' 這一欄進行計算，避免維度錯誤
                    close_series = df['Close'].squeeze()
                    
                    # 計算指標
                    df['MA20'] = close_series.rolling(window=20).mean()
                    df['STD20'] = close_series.rolling(window=20).std()
                    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
                    
                    last_price = float(close_series.iloc[-1])
                    ma20 = float(df['MA20'].iloc[-1])
                    upper_band = float(df['Upper'].iloc[-1])
                    
                    # 取得中文名稱
                    ticker = yf.Ticker(search_symbol)
                    name = ticker.info.get('longName', raw_symbol)
                    
                    st.success(f"掃描對象：{name}")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("當前股價", f"{last_price:.2f}")
                    m2.metric("20MA (月線)", f"{ma20:.2f}")
                    m3.metric("布林上軌", f"{upper_band:.2f}")

                    st.subheader("🛡️ 英雄決策建議")
                    if last_price > upper_band:
                        st.warning("⚠️ **高檔警戒**：股價已衝破布林上軌！請注意乖離過大風險。")
                    elif last_price > ma20:
                        st.info("🔥 **動能持續**：股價在月線之上，維持強勢慣性。")
                    else:
                        st.error("❄️ **保守觀望**：股價跌破月線，動能轉弱。")
                        
                    # 顯示圖表
                    st.line_chart(df[['Close', 'MA20', 'Upper']])
                    
                else:
                    st.error("找不到資料，請確認代碼是否正確。")
                    
            except Exception as e:
                st.error(f"系統異常: {e}")

    st.write("---")
    st.caption("💡 專為英雄手機端設計，建議一次輸入一個代碼以獲得最佳精準度。")
