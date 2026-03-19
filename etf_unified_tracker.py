import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime

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
    requests.post(url, data=payload)

def fetch_and_send():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    results = []
    
    for ticker in TICKERS:
        try:
            # 5년치 데이터를 가져와서 에러 없이 안전하게 계산 (1년=약 252거래일)
            df = yf.download(ticker, period="5y", interval="1d", progress=False)
            if df.empty or len(df) < 252: continue
            
            cp = float(df['Close'].iloc[-1])
            
            # 고점 계산 (1년, 2년, 3년)
            h_1y = float(df['High'].iloc[-252:].max()) if len(df) >= 252 else cp
            h_2y = float(df['High'].iloc[-504:].max()) if len(df) >= 504 else h_1y
            h_3y = float(df['High'].iloc[-756:].max()) if len(df) >= 756 else h_2y
            
            # 저점 계산 (1년, 2년, 3년)
            l_1y = float(df['Low'].iloc[-252:].min()) if len(df) >= 252 else cp
            l_2y = float(df['Low'].iloc[-504:].min()) if len(df) >= 504 else l_1y
            l_3y = float(df['Low'].iloc[-756:].min()) if len(df) >= 756 else l_2y
            
            # MDD 및 상승률 계산
            m1 = ((cp - h_1y) / h_1y) * 100
            m2 = ((cp - h_2y) / h_2y) * 100
            m3 = ((cp - h_3y) / h_3y) * 100
            
            g1 = ((cp - l_1y) / l_1y) * 100
            g2 = ((cp - l_2y) / l_2y) * 100
            g3 = ((cp - l_3y) / l_3y) * 100
            
            # 점수 부여 및 상태 결정 (정렬을 위해 Score 부여)
            if m1 <= -60.0 or g1 <= 15.0:
                score = 3
                status = "🔥 적극매수"
            elif m1 <= -30.0 or g1 <= 40.0:
                score = 2
                status = "🟢 매수"
            else:
                score = 1
                status = "🟡 진입"
            
            results.append({
                "ETF": ticker, "Price": round(cp, 2), "Status": status, "Score": score,
                "M1": round(m1, 1), "M2": round(m2, 1), "M3": round(m3, 1),
                "G1": round(g1, 1), "G2": round(g2, 1), "G3": round(g3, 1)
            })
        except: continue

    if results:
        # 가장 중요한 'Score' 기준으로 내림차순 정렬 (🔥적극매수 -> 🟢매수 -> 🟡진입)
        results.sort(key=lambda x: x['Score'], reverse=True)
        
        # 가독성을 위해 10개씩 메시지를 분할하여 전송 (400 에러 원천 차단)
        chunk_size = 10
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i + chunk_size]
            part = (i // chunk_size) + 1
            total_parts = (len(results) - 1) // chunk_size + 1
            
            msg = f"<b>🚀 ETF 리스크/기회 리포트 ({part}/{total_parts})</b>\n"
            msg += f"기준: {current_ny_time} (NYT)\n\n"
            
            for row in chunk:
                msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
                msg += f"🔻 MDD: 1년 {row['M1']}% | 2년 {row['M2']}% | 3년 {row['M3']}%\n"
                msg += f"🔺 Gain: 1년 +{row['G1']}% | 2년 +{row['G2']}% | 3년 +{row['G3']}%\n"
                msg += f"---------------------------------\n"
            
            send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send()
