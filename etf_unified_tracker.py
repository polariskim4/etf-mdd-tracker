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
    if res.status_code != 200:
        print(f"상세 에러: {res.text}")

def fetch_and_send():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    date_3y = (datetime.now() - timedelta(days=3*365))
    date_1y = (datetime.now() - timedelta(days=1*365))
    
    results = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="5y", interval="1d", progress=False)
            if df.empty: continue
            
            cp = df['Close'].iloc[-1]
            df.index = df.index.tz_localize(None)
            
            h_1y = df[df.index >= date_1y]
            h_3y = df[df.index >= date_3y]

            mdd_1 = ((cp - h_1y['High'].max()) / h_1y['High'].max()) * 100
            mdd_3 = ((cp - h_3y['High'].max()) / h_3y['High'].max()) * 100
            
            # Score 계산 (정렬용)
            score = 3 if mdd_1 <= -60.0 else (2 if mdd_1 <= -30.0 else 1)
            status = "🔥 적극매수" if score == 3 else ("🟢 매수" if score == 2 else "🟡 진입")
            
            results.append({
                "ETF": ticker, "Price": round(float(cp), 2), "Status": status, "Score": score,
                "MDD1": round(float(mdd_1), 1), "MDD3": round(float(mdd_3), 1)
            })
        except: continue

    if results:
        results.sort(key=lambda x: x['Score'], reverse=True)
        
        # 메시지를 15개씩 나누어 전송 (400 에러 방지)
        chunk_size = 15
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i + chunk_size]
            msg = f"<b>🚀 ETF 리포트 ({i//chunk_size + 1}부)</b>\n"
            msg += f"기준: {current_ny_time}\n\n"
            for row in chunk:
                msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
                msg += f"🔻 MDD: 1년 {row['MDD1']}% / 3년 {row['MDD3']}%\n"
                msg += f"----------------------------------\n"
            send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send()
