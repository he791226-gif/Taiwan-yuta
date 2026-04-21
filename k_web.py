import sys
import getpass

def check_password():
    # 在這裡設定你想要的密碼
    SECRET_PASSWORD = "你的密碼" 
    
    # 使用 getpass 讓輸入密碼時不會顯示在螢幕上，避免被旁人看到
    pwd = getpass.getpass("請輸入系統啟動密碼: ")
    
    if pwd == SECRET_PASSWORD:
        print("\n[密碼正確] 系統啟動中...")
        return True
    else:
        print("\n[錯誤] 密碼不正確，存取拒絕。")
        return False

def pro_stock_monitor():
    print("\n" + "="*50)
    print("      2436 偉詮電 進階動態監控系統 (密碼防護版)      ")
    print("="*50)
    
    try:
        # 1. 昨天的靜態數據 (今晚就可以先填好)
        y_close = float(input("1. 請輸入昨日收盤價 (如 75.1): "))
        y_total_vol = float(input("2. 請輸入昨日總成交量 (張): "))
        
        # 自動計算攻擊門檻 (昨日總量 8%)
        suggested_threshold = y_total_vol * 0.08
        print(f"\n[系統計算] 明日 5 分鐘強勢門檻建議: {suggested_threshold:.0f} 張")
        
        ref_input = input(f"   請輸入門檻 (按 Enter 使用建議值 {suggested_threshold:.0f}): ")
        ref_volume = float(ref_input) if ref_input else suggested_threshold

        print("\n" + "-"*50)
        print("設定完成。請於明天 9:00 - 9:30 輸入實時數據。")
        print("-"*50)

        # 2. 明天早上的即時開盤價
        t_open = float(input("3. 請輸入今日開盤價 (9:25確認): "))
        premium_rate = ((t_open - y_close) / y_close) * 100
        
        print(f"\n[目前狀態] 開盤溢價率: {premium_rate:.2f}%")
        
        # 3. 關鍵的 5 分鐘成交量
        current_vol = float(input("4. 請輸入開盤前 5-10 分鐘累計成交量 (張): "))

        # 4. 核心邏輯診斷
        status = ""
        suggestion = ""

        if premium_rate < 0:
            status = "危險 (負溢價)"
            suggestion = "主力出貨嫌疑重，不符強勢股慣性，建議開盤先撤。"
            
        elif 0 <= premium_rate < 3:
            if current_vol >= ref_volume:
                status = "弱勢轉強 (量能救援！)"
                suggestion = f"開盤溢價雖低({premium_rate:.2f}%)，但量能達標，主力強勢換手，符合「放量上攻」，建議續抱！"
            else:
                status = "真弱勢 (氣勢不足且無量)"
                suggestion = "低溢價且量能不足，容易開平走低，建議保守減碼。"
                
        elif 3 <= premium_rate <= 5:
            status = "健康走勢"
            suggestion = "開盤氣勢良好，穩健續抱。注意盤中若衝高至 6-8% 可分批獲利了結。"
            
        elif premium_rate > 5:
            status = "極強氣勢 (主力搶購)"
            suggestion = f"溢價高達 {premium_rate:.2f}%！力道極強，只要不跌回 3% 溢價位置，有機會拚連板。"

        # 5. 最終結果輸出
        print("\n" + "★"*45)
        print(f"  最終診斷結果：{status}")
        print(f"  建議操作策略：{suggestion}")
        print("★"*45)

    except ValueError:
        print("\n[錯誤] 輸入格式有誤，請輸入數字。")

if __name__ == "__main__":
    # 執行程式後先驗證密碼
    if check_password():
        pro_stock_monitor()
    else:
        sys.exit()
