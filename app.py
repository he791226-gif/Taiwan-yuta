import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# --- 英雄名冊：中文對照名單 (不刪減任何你有的邏輯) ---
NAME_MAP = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "1905": "華紙",
    "1906": "達新", "2449": "京元電子", "2368": "金像電", "4558": "永新-KY",
    "2303": "聯電", "2881": "富邦金", "2882": "國泰金", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2409": "友達", "3481": "群創"
}

# 2. 授權登入
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwei8888": # <--- 請在此修改密碼
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
else:
    # --- 獲取美股三大指數 (S&P500, Nasdaq, 費半) ---
    @st.cache_data(ttl=3600)
    def get_us_market_all():
        try:
            # ^GSPC: S&P 500, ^IXIC: Nasdaq, ^SOX: Philadelphia Semiconductor
            indices = ["^GSPC", "^IXIC", "^SOX"]
            data = yf.download(indices, period="2d", progress=False)['Close']
            
            changes = []
            for col in data.columns:
                change = ((data[col].iloc[-1] - data[col].iloc[-2]) / data[col].iloc[-2] * 100)
                changes.append(change)
            
            # 綜合情緒加權：費半 40%, Nasdaq 40%, S&P 20% (因為你偏好科技與波動)
            total_sentiment = (changes[2] * 0.4) + (changes[1] * 0.4) + (changes[0] * 0.2)
            return total_sentiment, changes[1], changes[2] # 傳回綜合、那指、費半
        except: return 0, 0, 0

    us_total, nasdaq_chg, sox_chg = get_us_market_all()
    
    st.title("🚀 台股英雄手機監控台")
    
    # 顯示美股儀表板
    us_col1, us_col2, us_col3 = st.columns(3)
    us_col1.metric("美股綜合情緒", f"{us_total:.2f}%", delta_color="normal")
    us_col2.metric("那斯達克 (Nasdaq)", f"{nasdaq_chg:.2f}%")
    us_col3.metric("費城半導體 (SOX)", f"{sox_chg:.2f}%")
    
    if us_total < -1.5:
        st.error(f"⚠️ 警告：昨晚美股大震盪，台股開盤壓力極大，系統已自動調高防禦權重。")

    symbol_input = st.text_input("輸入股票代碼 (可用空格分開)", "1905 2449 2330")
    
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
                        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

                        # --- 數據計算 ---
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
                        change_pct = ((curr_price - prev_price) / prev_price) * 100
                        change_text = f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%"

                        # --- 英雄核心評分大腦 (加入美股因子與縮量判定) ---
                        score = 65 
                        
                        # A. 當日動能 (漲停加分, 跌停重罰)
                        if change_pct > 8: score += 20
                        elif change_pct < -9: score -= 45 # 跌停是崩壞
                        elif change_pct < -5: score -= 25

                        # B. 美股外部環境連動 (關鍵修正：環境不好, 分數自動打折)
                        if us_total < -1: score -= 15
                        elif us_total > 1: score += 10

                        # C. 縮量與爆量判定 (修正華紙問題)
                        is_volume_spike = curr_vol > curr_ma5v * 1.2
                        if change_pct < -5:
                            if not is_volume_spike:
                                score -= 20 # 縮量重挫 = 無支撐陰跌 (最危險)
                                vol_tag = "⚠️ 縮量下殺 (警訊)"
                            else:
                                score -= 15 # 爆量大跌 = 逃命潮
                                vol_tag = "🆘 逃命爆量"
                        else:
                            vol_tag = "🔥 攻擊爆量" if is_volume_spike and change_pct > 0 else "💎 量能平穩"

                        # D. 位階判定
                        if curr_price < ma20.iloc[-1]:
                            score -= 10 if change_pct > 5 else 20 # 沒站上月線前都是守勢

                        final_score = int(min(99, max(5, score)))

                        # --- UI 呈現 ---
                        name = NAME_MAP.get(raw_symbol, "未知")
                        st.markdown(f"### 🛡️ {name} ({raw_symbol})")
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            p_color = "#ff4b4b" if change_pct > 0 else "#00cc00"
                            st.markdown(f"現價 (今日漲跌: <span style='color:{p_color}; font-weight:bold;'>{change_text}</span>)", unsafe_allow_html=True)
                            st.title(f"$ {curr_price:.2f}")
                            s_color = "#ff4b4b" if final_score > 70 else ("#00cc00" if final_score < 40 else "#31333F")
                            st.markdown(f"攻擊力點數: <h1 style='color:{s_color}; font-size: 70px;'>{final_score}</h1>", unsafe_allow_html=True)
                            
                            prob = "極高" if final_score >= 85 else ("高" if final_score >= 70 else "普通" if final_score >= 50 else "低")
                            st.write(f"明日噴發機率：**{prob}**")

                        with col2:
                            # 專業標籤
                            if curr_price < ma20.iloc[-1]:
                                if change_pct > 5: st.warning("⚡ 市場對比：跌勢反彈 (觀望)")
                                else: st.error("❌ 市場對比：弱於大盤 (破線)")
                            else: st.success("✅ 市場對比：強於大盤")
                            
                            # 量能描述更新
                            if "縮量" in vol_tag: st.markdown(f"<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'>{vol_tag}</div>", unsafe_allow_html=True)
                            elif "逃命" in vol_tag: st.markdown(f"<div style='background-color:#e6ffe6; padding:10px; border-radius:5px;'>{vol_tag}</div>", unsafe_allow_html=True)
                            elif "攻擊" in vol_tag: st.markdown(f"<div style='background-color:#ffe6e6; padding:10px; border-radius:5px;'>{vol_tag}</div>", unsafe_allow_html=True)
                            else: st.info(f"💎 {vol_tag}")

                            st.warning(f"🚀 趨勢型態：{'多頭強攻' if curr_price > upper.iloc[-1] else ('空頭反轉' if change_pct < -5 else '區間震盪')}")
                            st.info(f"⚡ 動能指標：{'動能潰散' if change_pct < -5 else '持續加溫'}")

                        st.line_chart(pd.DataFrame({'Close': close, 'MA20': ma20}).tail(40))
                        st.markdown("---")
                except Exception as e:
                    st.error(f"{raw_symbol} 異常: {e}")
