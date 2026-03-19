import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime, timedelta

# Secrets 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TICKERS = [
    "TQQQ", "SOXL", "SPXL", "UPRO", "TECL", "FAS", "FNGU", "TNA", "KORU", "NUGT",
    "YINN", "UDOW", "LABU", "NAIL", "DFEN", "DPST", "ERX", "URTY", "EDC", "CURE",
    "BRZU", "EURL", "INDL", "DRN", "DUSL", "UTSL", "MEXX", "TPOR", "PILL", "BITU", "ETHT"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, data=payload)
    print(f"Telegram 전송 결과: {res.status_code}")

def get_status(mdd_1y, rec_1y):
    if mdd_1y <= -60.0 or rec_1y <= 15.0: return (3, "🔥 적극매수")
    elif mdd_1y <= -30.0 or rec_1y <= 40.0: return (2, "🟢 매수")
    else: return (1, "🟡 진입")

def fetch_and_send():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 넉넉하게 4년치 데이터를 가져와서 기간별로 자릅니다 (데이터 유실 방지)
    start_date = (datetime.now() - timedelta(days=4*365)).strftime('%Y-%m-%d')
    date_3y = (datetime.now() - timedelta(days=3*365))
    date_2y = (datetime.now() - timedelta(days=2*365))
    date_1y = (datetime.now() - timedelta(days=1*365))
    
    results = []
    print(f"데이터 수집 시작: {len(TICKERS)}개 종목")

    for ticker in TICKERS:
        try:
            etf = yf.Ticker(ticker)
            # 기간을 통째로 가져온 후 내부에서 처리 (성능 및 안정성 향상)
            hist = etf.history(period="5y") 
            if hist.empty or len(hist) < 10:
                print(f"[{ticker}] 데이터가 부족합니다.")
                continue
            
            cp = hist['Close'].iloc[-1]

            # 타임존 제거 (비교를 위해)
            hist.index = hist.index.tz_localize(None)
            
            # 기간별 데이터 슬라이싱
            h_1y = hist[hist.index >= date_1y]
            h_2y = hist[hist.index >= date_2y]
            h_3y = hist[hist.index >= date_3y]

            mdd = [
                ((cp - h_1y['High'].max()) / h_1y['High'].max()) * 100,
                ((cp - h_2y['High'].max()) / h_2y['High'].max()) * 100,
                ((cp - h_3y['High'].max()) / h_3y['High'].max()) * 100
            ]
            gain = [
                ((cp - h_1y['Low'].min()) / h_1y['Low'].min()) * 100,
                ((cp - h_2y['Low'].min()) / h_2y['Low'].min()) * 100,
                ((cp - h_3y['Low'].min()) / h_3y['Low'].min()) * 100
            ]
            
            score, label = get_status(mdd[0], gain[0])
            results.append({
                "ETF": ticker, "Price": round(cp, 2), "Score": score, "Status": label,
                "MDD": [round(x, 1) for x in mdd], "Gain": [round(x, 1) for x in gain]
            })
            print(f"[{ticker}] 처리 완료")
        except Exception as e:
            print(f"[{ticker}] 에러 발생: {e}")

    if results:
        df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
        msg = f"<b>🚀 통합 ETF 리포트 (추천순)</b>\n기준: {current_ny_time} (NYT)\n\n"
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
            msg += f"🔻 <b>MDD:</b> 1년 {row['MDD'][0]}% / 2년 {row['MDD'][1]}% / 3년 {row['MDD'][2]}%\n"
            msg += f"🔺 <b>Gain:</b> 1년 +{row['Gain'][0]}% / 2년 +{row['Gain'][1]}% / 3년 +{row['Gain'][2]}%\n"
            msg += f"----------------------------------\n"
        
        send_telegram_message(msg)
        print("모든 메시지 전송 완료!")
    else:
        print("전송할 결과 데이터가 없습니다.")

if __name__ == "__main__":
    fetch_and_send()
