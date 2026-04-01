import streamlit as st
import yfinance as yf
import pandas as pd

# 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 簡單密碼鎖
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 英雄系統手機授權")
        pwd = st.text_input("輸入授權密碼", type="password")
        if st.button("登入"):
            if pwd == "yuwai8888": # 請記得把這裡改成你之前的密碼
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密碼錯誤")
        return False
    return True

if check_password():
    st.title("🚀 台股英雄手機監控台")
    
    symbol = st.text_input("輸入股票代碼 (例如: 1905, 2330)", "1905")
    
    if st.button("開始英雄掃描"):
        with st.spinner("正在連接雲端數據庫..."):
            try:
                # 如果你沒打 .TW，程式幫你補上
if ".TW" not in symbol.upper() and ".TWO" not in symbol.upper():
    search_symbol = f"{symbol}.TW"
else:
    search_symbol = symbol

df = yf.download(search_symbol, period="6mo", interval="1d")
                
                if not df.empty:
                    # 1. 計算 20MA (月線) - 純手寫邏輯
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    # 2. 計算 20MA 標準差
                    df['STD20'] = df['Close'].rolling(window=20).std()
                    # 3. 計算 Bollinger Bands (布林通道)
                    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
                    
                    last_price = float(df['Close'].iloc[-1])
                    ma20 = float(df['MA20'].iloc[-1])
                    upper_band = float(df['Upper'].iloc[-1])
                    
                    # 取得中文名稱 (yfinance 抓取)
                    info = yf.Ticker(f"{symbol}.TW").info
                    name = info.get('longName', symbol)
                    
                    st.success(f"掃描對象：{name}")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("當前股價", f"{last_price:.2f}")
                    col2.metric("20MA (月線)", f"{ma20:.2f}")
                    col3.metric("布林上軌", f"{upper_band:.2f}")

                    # --- 避險與動能邏輯 ---
                    st.subheader("🛡️ 英雄決策建議")
                    
                    # 判斷是否過熱 (股價離上軌太遠)
                    if last_price > upper_band * 1.05:
                        st.warning("⚠️ 高檔警戒：股價已噴出布林上軌過多，請注意回檔風險！")
                    elif last_price > ma20:
                        st.info("🔥 動能持續：股價站穩月線之上，具備英雄特質。")
                    else:
                        st.error("❄️ 整理階段：股價低於月線，建議觀望。")
                        
                    # 顯示簡易K線表
                    st.line_chart(df[['Close', 'MA20', 'Upper']])
                    
                else:
                    st.error("找不到這檔股票，請確認代碼是否正確。")
            except Exception as e:
                st.error(f"發生錯誤: {e}")

    st.write("---")
    st.caption("本系統僅供技術分析參考，投資請自行評估風險。")
