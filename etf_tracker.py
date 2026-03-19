import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime

# GitHub Secrets에서 정보를 가져오도록 수정
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
    requests.post(url, data=payload)

def get_status_icon(drawdown_pct):
    if drawdown_pct >= -30.0: return "🟡 진입"
    elif drawdown_pct >= -60.0: return "🟢 매수"
    else: return "🔥 적극매수"

def fetch_and_send_data():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    results = []
    for ticker in TICKERS:
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="max")
            if hist.empty: continue
            ath = hist['Close'].max()
            current_price = hist['Close'].iloc[-1]
            drawdown = ((current_price - ath) / ath) * 100
            results.append({"ETF": ticker, "전고점": round(ath, 2), "현재가": round(current_price, 2), "하락률": round(drawdown, 2), "전략": get_status_icon(drawdown)})
        except: continue

    if results:
        df = pd.DataFrame(results).sort_values(by="하락률", ascending=True)
        msg = f"<b>📊 레버리지 ETF 하락률 리포트</b>\n기준: {current_ny_time} (NYT)\n\n"
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> : {row['하락률']}% {row['전략']}\n└ 현재: ${row['현재가']} / 전고점: ${row['전고점']}\n\n"
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_data()
