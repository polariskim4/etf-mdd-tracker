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

def get_status_icon(mdd_pct):
    """하락률이 클수록 매수 권장 (1년 MDD 기준)"""
    if mdd_pct <= -60.0: return "🔥 적극매수" # -60% 이상 폭락
    elif mdd_pct <= -30.0: return "🟢 매수"     # -30% 이상 조정
    else: return "🟡 진입"                    # 완만한 하락

def fetch_and_send_mdd_data():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 기간 설정
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

            # 1년, 2년, 3년 내 최고점(High) 찾기
            ath_1y = hist[hist.index >= date_1y]['High'].max()
            ath_2y = hist[hist.index >= date_2y]['High'].max()
            ath_3y = hist['High'].max()

            # 고점 대비 하락률(MDD) 계산
            mdd_1y = ((current_price - ath_1y) / ath_1y) * 100
            mdd_2y = ((current_price - ath_2y) / ath_2y) * 100
            mdd_3y = ((current_price - ath_3y) / ath_3y) * 100
            
            results.append({
                "ETF": ticker,
                "현재가": round(current_price, 2),
                "1년": round(mdd_1y, 1),
                "2년": round(mdd_2y, 1),
                "3년": round(mdd_3y, 1),
                "전략": get_status_icon(mdd_1y)
            })
        except: continue

    if results:
        # 1년 하락률이 가장 큰 순서(많이 떨어진 순)로 정렬
        df = pd.DataFrame(results).sort_values(by="1년", ascending=True)
        
        msg = f"<b>📉 ETF 기간별 고점 대비 하락률(MDD)</b>\n"
        msg += f"기준: {current_ny_time} (NYT)\n\n"
        
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> (현재 ${row['현재가']}) {row['전략']}\n"
            msg += f"└ 1년고점 대비: <b>{row['1년']}%</b>\n"
            msg += f"└ 2년고점 대비: {row['2년']}%\n"
            msg += f"└ 3년고점 대비: {row['3년']}%\n\n"
        
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_mdd_data()
