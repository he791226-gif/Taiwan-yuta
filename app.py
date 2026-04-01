import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# --- 英雄名冊：前 500 大常用名對照 (已內建常用代碼，可自行擴充) ---
NAME_MAP = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "1905": "華紙",
    "1906": "達新", "2449": "京元電子", "2368": "金像電", "4558": "永新-KY",
    "2303": "聯電", "2881": "富邦金", "2882": "國泰金", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2409": "友達", "3481": "群創",
    "3037": "欣興", "2379": "瑞昱", "2382": "廣達", "2357": "華碩"
}

# 2. 密碼鎖 (保護你的英雄策略)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "yuwei8888": # <--- 請在此修改你的登入密碼
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤，請重新輸入")
else:
    st.title("🚀 台股英雄手機監控台")
    symbol_input = st.text_input("輸入股票代碼 (可用空格分開多個)", "2449 1906 2330")
    
    if st.button("開始英雄掃描"):
        symbols = symbol_input.strip().split()
        
        for raw_symbol in symbols:
            with st.container():
                try:
                    # 判斷上市或上櫃
                    search_symbol = f"{raw_symbol}.TW"
                    df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)
                    if df.empty:
                        search_symbol = f"{raw_symbol}.TWO"
                        df = yf.download(search_symbol, period="6mo", interval="1d", progress=False)

                    if not df.empty:
                        # 處理 yfinance 多重索引問題
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
                        
                        # 漲跌與趨勢判斷
                        change_pct = ((curr_price - prev_price) / prev_price) * 100
                        change_text = f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%"
                        is_crashing = change_pct < -4  # 定義明顯下跌
                        is_soaring = change_pct > 4    # 定義明顯上漲
                        is_below_ma20 = curr_price < ma20.iloc[-1]

                        # --- 英雄評分大腦 (深度調適邏輯) ---
                        score = 65 
                        # A. 漲跌動能權重
                        if change_pct > 7: score += 20
                        elif change_pct > 3: score += 10
                        elif change_pct < -7: score -= 30
                        elif change_pct < -3: score -= 15

                        # B. 趨勢位階權重
                        if curr_price > upper.iloc[-1]: score += 15 # 噴發
                        if is_below_ma20:
                            # 若大漲反彈則扣分減輕
                            score -= 10 if change_pct > 5 else 25 

                        # C. 量能配合判定
                        if curr_vol > curr_ma5v * 1.5:
                            score += (15 if change_pct > 0 else -20)

                        final_score = int(min(99, max(5, score)))

                        # --- UI 顯示區 ---
                        name = NAME_MAP.get(raw_symbol, "搜尋中...")
                        st.markdown(f"### 🛡️ {name} ({raw_symbol})")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            # 漲紅跌綠顏色標示
                            p_color = "#ff4b4b" if change_pct > 0 else "#00cc00"
                            st.markdown(f"現價 (今日漲跌: <span style='color:{p_color}; font-weight:bold;'>{change_text}</span>)", unsafe_allow_html=True)
                            st.title(f"$ {curr_price:.2f}")
                            
                            # 分數顏色標示
                            s_color = "#ff4b4b" if final_score > 70 else ("#00cc00" if final_score < 40 else "#31333F")
                            st.markdown(f"攻擊力點數: <h1 style='color:{s_color}; font-size: 70px;'>{final_score}</h1>", unsafe_allow_html=True)
                            
                            prob = "極高" if final_score >= 85 else ("高" if final_score >= 70 else ("普通" if final_score >= 50 else "低"))
                            st.write(f"明日噴發機率：**{prob}**")

                        with col2:
                            # 狀態標籤判定
                            if is_below_ma20:
                                if change_pct > 5: st.warning("⚡ 市場對比：跌勢反彈 (強勢中)")
                                else: st.error("❌ 市場對比：弱於大盤 (破線)")
                            else: st.success("✅ 市場對比：強於大盤")

                            if curr_vol > curr_ma5v * 1.2:
                                if change_pct > 0: st.markdown("<div style='background-color:#ffe6e6; padding:10px; border-radius:5px;'>🔥 攻擊爆量</div>", unsafe_allow_html=True)
                                else: st.markdown("<div style='background-color:#e6ffe6; padding:10px; border-radius:5px;'>🆘 逃命爆量</div>", unsafe_allow_html=True)
                            else: st.info("💎 量能強度：縮量整理")

                            st.warning(f"🚀 趨勢型態：{'多頭強攻' if curr_price > upper.iloc[-1] and not is_crashing else ('空頭反轉' if is_crashing else '區間震盪')}")
                            st.info(f"⚡ 動能指標：{'動能潰散' if is_crashing else '持續加溫'}")

                        # 圖表中文化標籤
                        df_plot = pd.DataFrame({
                            '收盤價(Close)': close,
                            '月線(MA20)': ma20,
                            '布林上軌(Upper)': upper
                        }).tail(60)
                        st.line_chart(df_plot)
                        st.markdown("---")
                        
                except Exception as e:
                    st.error(f"{raw_symbol} 異常: {e}")
