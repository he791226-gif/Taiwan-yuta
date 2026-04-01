import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# 2. 簡單密碼鎖 (確保只有你能用)
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 英雄系統手機授權")
        # --- 請在此修改你的登入密碼 ---
        pwd = st.text_input("輸入授權密碼", type="password")
        if st.button("登入"):
            if pwd == "你的密碼":  # <--- 把這裡改成你想設定的密碼
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密碼錯誤，請重新輸入")
        return False
    return True

if check_password():
    st.title("🚀 台股英雄手機監控台")
    st.markdown("---")
    
    # 3. 輸入介面
    symbol_input = st.text_input("輸入股票代碼 (例: 1905, 2330)", "1905")
    
    if st.button("開始英雄掃描"):
        with st.spinner("正在抓取最新數據..."):
            try:
                # 自動判斷台股後綴邏輯
                symbol = symbol_input.strip()
                if not (symbol.endswith(".TW") or symbol.endswith(".TWO")):
                    # 先嘗試上市 (.TW)，抓不到資料再嘗試上櫃 (.TWO)
                    search_symbol = f"{symbol}.TW"
                else:
                    search_symbol = symbol

                # 抓取 6 個月內的日線資料
                df = yf.download(search_symbol, period="6mo", interval="1d")
                
                # 如果上市抓不到，自動換成上櫃試試
                if df.empty and ".TW" in search_symbol:
                    search_symbol = f"{symbol}.TWO"
                    df = yf.download(search_symbol, period="6mo", interval="1d")

                if not df.empty:
                    # 4. 指標計算 (純 Pandas 邏輯，避開 TA-Lib 安裝問題)
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    df['STD20'] = df['Close'].rolling(window=20).std()
                    df['Upper'] = df['MA20'] + (df['STD20'] * 2)
                    df['Lower'] = df['MA20'] - (df['STD20'] * 2)
                    
                    # 取得最新一筆數據
                    last_price = float(df['Close'].iloc[-1])
                    ma20 = float(df['MA20'].iloc[-1])
                    upper_band = float(df['Upper'].iloc[-1])
                    
                    # 取得公司名稱
                    ticker_info = yf.Ticker(search_symbol).info
                    chinese_name = ticker_info.get('longName', symbol)
                    
                    # 5. 數據面板展示
                    st.success(f"掃描對象：{chinese_name} ({search_symbol})")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("當前股價", f"{last_price:.2f}")
                    m2.metric("20MA (月線)", f"{ma20:.2f}")
                    m3.metric("布林上軌 (壓力)", f"{upper_band:.2f}")

                    # 6. 英雄決策邏輯 (避開高檔震盪風險)
                    st.subheader("🛡️ 英雄決策建議")
                    
                    # 計算乖離與布林位置
                    if last_price > upper_band:
                        st.warning("⚠️ **高檔警戒**：股價已衝破布林上軌！目前處於極端過熱區，請慎防回檔風險。")
                    elif last_price > ma20:
                        st.info("🔥 **動能持續**：股價站穩月線之上，符合強勢動能慣性。")
                    else:
                        st.error("❄️ **保守觀望**：股價目前跌破月線，短線動能不足，建議等待止跌。")
                        
                    # 7. 視覺化圖表
                    st.line_chart(df[['Close', 'MA20', 'Upper']])
                    
                else:
                    st.error(f"錯誤：找不到代碼 {symbol} 的資料，請確認代碼是否正確。")
                    
            except Exception as e:
                st.error(f"系統異常: {str(e)}")

    st.write("---")
    st.caption("💡 提示：本工具專為手機優化，建議點擊瀏覽器「加入主畫面」當作 App 使用。")
