import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime, timedelta

# GitHub Secrets
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

def get_status(mdd_1y, rec_1y):
    """매수 강도에 따른 숫자 부여 (정렬용)"""
    if mdd_1y <= -60.0 or rec_1y <= 15.0:
        return (3, "🔥 적극매수")
    elif mdd_1y <= -30.0 or rec_1y <= 40.0:
        return (2, "🟢 매수")
    else:
        return (1, "🟡 진입")

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

            # 고점(High) 및 저점(Low) 추출
            ath_1y = hist[hist.index >= date_1y]['High'].max()
            ath_2y = hist[hist.index >= date_2y]['High'].max()
            ath_3y = hist['High'].max()
            
            low_1y = hist[hist.index >= date_1y]['Low'].min()
            low_2y = hist[hist.index >= date_2y]['Low'].min()
            low_3y = hist['Low'].min()

            # 하락률/상승률 계산
            mdd = [((current_price - h) / h) * 100 for h in [ath_1y, ath_2y, ath_3y]]
            rec = [((current_price - l) / l) * 100 for l in [low_1y, low_2y, low_3y]]
            
            score, label = get_status(mdd[0], rec[0])
            
            results.append({
                "ETF": ticker, "Price": round(current_price, 2), 
                "Score": score, "Status": label,
                "MDD": [round(x, 1) for x in mdd],
                "Gain": [round(x, 1) for x in rec]
            })
        except: continue

    if results:
        # Score(적극매수 3점) 기준 내림차순 정렬
        df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
        
        msg = f"<b>🚀 통합 ETF 리포트 (추천순 정렬)</b>\n"
        msg += f"기준: {current_ny_time} (NYT)\n\n"
        
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
            msg += f"🔻 <b>MDD(고점):</b> 1년 {row['MDD'][0]}% / 2년 {row['MDD'][1]}% / 3년 {row['MDD'][2]}%\n"
            msg += f"🔺 <b>Gain(저점):</b> 1년 +{row['Gain'][0]}% / 2년 +{row['Gain'][1]}% / 3년 +{row['Gain'][2]}%\n"
            msg += f"----------------------------------\n"
        
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_unified_data()
