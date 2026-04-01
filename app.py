import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本設定
st.set_page_config(page_title="🚀 台股英雄手機監控台", layout="wide")

# --- 英雄名冊：中文對照名單 (絕對不刪減) ---
NAME_MAP = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "1905": "華紙",
    "1906": "達新", "2449": "京元電子", "2368": "金像電", "4558": "永新-KY",
    "2303": "聯電", "2881": "富邦金", "2882": "國泰金", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2409": "友達", "3481": "群創",
    "3037": "欣興", "2379": "瑞昱", "2382": "廣達", "2357": "華碩"
}

# 2. 授權登入
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 英雄系統手機授權")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "你的密碼":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
else:
    # --- 獲取美股三大指數 (情緒分析) ---
    @st.cache_data(ttl=3600)
    def get_us_market_sentiment():
        try:
            indices = ["^GSPC", "^IXIC", "^SOX"] # S&P500, Nasdaq, SOX
            data = yf.download(indices, period="2d", progress=False)['Close']
            changes = [((data[col].iloc[-1] - data[col].iloc[-2]) / data[col].iloc[-2] * 100) for col in data.columns]
            avg_chg = sum(changes) / len(changes)
            return avg_chg, changes[1], changes[2] # 綜合, Nasdaq, SOX
        except: return 0, 0, 0

    us_avg, nasdaq_chg, sox_chg = get_us_market_sentiment()

    st.title("🚀 台股英雄手機監控台")
    
    # 顯示美股儀表板
    us_c1, us_c2, us_c3 = st.columns(3)
    us_c1.metric("美股綜合情緒", f"{us_avg:.2f}%")
    us_c2.metric("那斯達克 (Nasdaq)", f"{nasdaq_chg:.2f}%")
    us_c3.metric("費半 (SOX)", f"{sox_chg:.2f}%")

    symbol_input = st.text_input("輸入股票代碼 (可用空格分開)", "1905 1906 2449")
    
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

                        # --- 關鍵數據計算 (全數回歸) ---
                        close = df['Close'].astype(float)
                        vol = df['Volume'].astype(float)
                        ma20 = close.rolling(window=20).mean()
                        std20 = close.rolling(window=20).std()
                        upper = ma20 + (std20 * 2)
                        lower = ma20 - (std20 * 2)
                        ma5_v = vol.rolling(window=5).mean()
                        
                        curr_price = float(close.iloc[-1])
                        prev_price = float(close.iloc[-2])
                        curr_ma20 = float(ma20.iloc[-1])
                        curr_upper = float(upper.iloc[-1])
                        curr_lower = float(lower.iloc[-1])
                        bias = ((curr_price - curr_ma20) / curr_ma20) * 100
                        change_pct = ((curr_price - prev_price) / prev_price) * 100

                        # --- 核心評分邏輯 (加入美股因子) ---
                        score = 65 
                        if change_pct > 7: score += 15
                        if change_pct < -9: score -= 35
                        if us_avg < -1.5: score -= 20 # 美股大跌加重扣分
                        
                        # 縮量判定
                        is_low_vol = float(vol.iloc[-1]) < float(ma5_v.iloc[-1])
                        if change_pct < -5 and is_low_vol: score -= 15 # 縮量跌停
                        
                        final_score = int(min(99, max(5, score)))

                        # --- UI 呈現 (嚴格對齊你的截圖需求) ---
                        name = NAME_MAP.get(raw_symbol, "未知")
                        st.markdown(f"### 🛡️ 英雄診斷：{name} ({raw_symbol})")
                        
                        # 頂部數值排版
                        val_c1, val_c2, val_c3, val_c4 = st.columns(4)
                        val_c1.write(f"**當前股價**\n# {curr_price:.2f}")
                        val_c2.write(f"**20MA (月線)**\n# {curr_ma20:.2f}")
                        val_c3.write(f"**布林上軌**\n# {curr_upper:.2f}")
                        val_c4.write(f"**月線乖離%**\n# {bias:.1f}%")

                        # 乖離率警告邏輯
                        if bias > 10:
                            st.warning(f"⚠️ 攻擊過熱：乖離率已達 {bias:.1f}% (正常值 < 10%)，建議分批獲利！")
                        elif bias < -10:
                            st.error(f"❄️ 乖離過低：股價超跌，注意反彈或持續下修風險。")

                        col1, col2 = st.columns([1, 1])
                        with col1:
                            s_color = "#ff4b4b" if final_score > 70 else ("#00cc00" if final_score < 40 else "#31333F")
                            st.markdown(f"攻擊力點數: <h1 style='color:{s_color}; font-size: 70px;'>{final_score}</h1>", unsafe_allow_html=True)
                            prob = "極高" if final_score >= 85 else ("高" if final_score >= 70 else "普通")
                            st.write(f"明日噴發機率：**{prob}**")

                        with col2:
                            if curr_price < curr_ma20: st.error("❌ 市場對比：弱於大盤 (破線)")
                            else: st.success("✅ 市場對比：強於大盤")
                            
                            if is_low_vol: st.info("💎 量能強度：縮量整理")
                            else: st.markdown("<div style='background-color:#ffe6e6; padding:10px;'>🔥 攻擊爆量</div>", unsafe_allow_html=True)
                            
                            st.warning(f"🚀 趨勢型態：{'多頭噴發' if curr_price > curr_upper else '區間震盪'}")
                            st.info(f"⚡ 動能指標：{'持續加溫' if change_pct > 0 else '動能潰散'}")

                        # 圖表回歸
                        chart_data = pd.DataFrame({
                            'Close': close,
                            'MA20': ma20,
                            'Upper': upper,
                            'Lower': lower
                        }).tail(50)
                        st.line_chart(chart_data)
                        st.markdown("---")
                except Exception as e:
                    st.error(f"{raw_symbol} 異常: {e}")
