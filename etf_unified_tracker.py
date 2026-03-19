import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime, timedelta

# GitHub Secrets 환경변수
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

def get_combined_status(mdd_1y, rec_1y):
    if mdd_1y <= -60.0 or rec_1y <= 15.0: return "🔥 적극매수"
    elif mdd_1y <= -30.0 or rec_1y <= 40.0: return "🟢 매수"
    else: return "🟡 진입"

def fetch_and_send_unified_data():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    date_3y = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    date_2y = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
    date_1y = (datetime.now() - timedelta(days=1*365)).strftime('%Y-%m-%d')
    
    results = []
    for ticker in TICKERS:
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(start=date_3y)
            if hist.empty: continue
            
            current_price = hist['Close'].iloc[-1]
            ath_1y, ath_2y, ath_3y = hist[hist.index >= date_1y]['High'].max(), hist[hist.index >= date_2y]['High'].max(), hist['High'].max()
            low_1y, low_2y, low_3y = hist[hist.index >= date_1y]['Low'].min(), hist[hist.index >= date_2y]['Low'].min(), hist['Low'].min()

            mdd_1y = ((current_price - ath_1y) / ath_1y) * 100
            rec_1y = ((current_price - low_1y) / low_1y) * 100
            
            results.append({
                "ETF": ticker, "Price": round(current_price, 2), "Status": get_combined_status(mdd_1y, rec_1y),
                "MDD": [round(mdd_1y, 1), round(((current_price-ath_2y)/ath_2y)*100, 1), round(((current_price-ath_3y)/ath_3y)*100, 1)],
                "Gain": [round(rec_1y, 1), round(((current_price-low_2y)/low_2y)*100, 1), round(((current_price-low_3y)/low_3y)*100, 1)]
            })
        except: continue

    if results:
        df = pd.DataFrame(results).sort_values(by="Status", ascending=False)
        msg = f"<b>🚀 통합 ETF 리스크/기회 리포트</b>\n기준: {current_ny_time} (NYT)\n\n"
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
            msg += f"🔻 <b>MDD(고점):</b> 1년 {row['MDD'][0]}% / 3년 {row['MDD'][2]}%\n"
            msg += f"🔺 <b>Gain(저점):</b> 1년 +{row['Gain'][0]}% / 3년 +{row['Gain'][2]}%\n"
            msg += f"----------------------------------\n"
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_unified_data()
