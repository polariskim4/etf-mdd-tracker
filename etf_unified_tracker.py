import yfinance as yf
import pandas as pd
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
    res = requests.post(url, data=payload)
    print(f"Telegram 전송 결과: {res.status_code}")

def fetch_and_send():
    results = []
    print("데이터 수집 시작...")

    for ticker in TICKERS:
        try:
            # 5년치 데이터를 가져와서 안전하게 처리
            df = yf.download(ticker, period="5y", interval="1d", progress=False)
            if df.empty or len(df) < 250: continue
            
            # 마지막 종가
            cp = float(df['Close'].iloc[-1])
            
            # 1년(약 252거래일), 3년(약 756거래일) 고점/저점 계산 (날짜 비교 에러 회피)
            h_1y_max = float(df['High'].iloc[-252:].max())
            h_3y_max = float(df['High'].iloc[-756:].max())
            
            mdd_1 = ((cp - h_1y_max) / h_1y_max) * 100
            mdd_3 = ((cp - h_3y_max) / h_3y_max) * 100
            
            # 점수 계산
            score = 3 if mdd_1 <= -60.0 else (2 if mdd_1 <= -30.0 else 1)
            status = "🔥 적극매수" if score == 3 else ("🟢 매수" if score == 2 else "🟡 진입")
            
            results.append({
                "ETF": ticker, "Price": round(cp, 2), "Status": status, "Score": score,
                "MDD1": round(mdd_1, 1), "MDD3": round(mdd_3, 1)
            })
            print(f"[{ticker}] 완료")
        except Exception as e:
            print(f"[{ticker}] 건너뜀 (사유: {e})")

    if results:
        # Score 기준 내림차순 정렬
        results.sort(key=lambda x: x['Score'], reverse=True)
        
        # 메시지를 15개씩 분할 전송 (400 에러 방지)
        chunk_size = 15
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i + chunk_size]
            msg = f"<b>🚀 ETF 리포트 ({i//chunk_size + 1}부)</b>\n\n"
            for row in chunk:
                msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
                msg += f"🔻 MDD: 1년 {row['MDD1']}% / 3년 {row['MDD3']}%\n"
                msg += f"----------------------------------\n"
            send_telegram_message(msg)
        print("모든 작업 완료!")
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    fetch_and_send()
