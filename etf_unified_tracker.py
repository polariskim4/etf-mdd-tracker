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
    "AAPU", "AGQ", "AMDL", "AMZU", "APPX", "ASTX", "AVL", "AVGX", "BABX", "BITI", 
    "BITU", "BMNU", "BOIL", "BRZU", "CONL", "CURE", "CWEB", "DDM", "DFEN", "DIG", 
    "DOG", "DPST", "DRIP", "DRN", "DSPY", "DUSL", "EDC", "ERX", "ETHT", "EURL", 
    "FAS", "FAZ", "FBL", "FNGO", "FNGS", "FNGU", "GGLL", "GLL", "GUSH", "INDL", 
    "IONX", "JNUG", "KOLD", "KORU", "LABU", "LITX", "METU", "MEXX", "MQQQ", "MSFU", 
    "MSTU", "MSTX", "MSTZ", "MULL", "MUU", "MVV", "NAIL", "NFXL", "NUGT", "NVDL", 
    "NVDU", "NVDX", "ORCX", "PILL", "PLTU", "PSQ", "PTIR", "QID", "QLD", "RKLX", 
    "ROM", "RWM", "SBIT", "SCO", "SDOW", "SDS", "SH", "SJB", "SNXX", "SOXL", 
    "SOXS", "SPDN", "SPXL", "SPXS", "SPXU", "SPUU", "SSO", "SQQQ", "SVXY", "TBT", 
    "TECL", "TMF", "TMV", "TNA", "TPOR", "TQQQ", "TSLL", "TSLQ", "TSLR", "TSLT", 
    "TSMX", "TSPY", "TZA", "UCO", "UDOW", "UGL", "UPRO", "URTY", "USD", "UTSL", 
    "UWM", "UYG", "YANG", "YINN", "ZSL"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, data=payload)
    print(f"Telegram 전송 결과: {res.status_code}")

def fetch_and_send():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    results = []
    
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="5y", interval="1d", progress=False)
            if df.empty or len(df) < 252: continue
            
            cp = float(df['Close'].iloc[-1])
            
            h_1y = float(df['High'].iloc[-252:].max()) if len(df) >= 252 else cp
            h_2y = float(df['High'].iloc[-504:].max()) if len(df) >= 504 else h_1y
            h_3y = float(df['High'].iloc[-756:].max()) if len(df) >= 756 else h_2y
            
            l_1y = float(df['Low'].iloc[-252:].min()) if len(df) >= 252 else cp
            l_2y = float(df['Low'].iloc[-504:].min()) if len(df) >= 504 else l_1y
            l_3y = float(df['Low'].iloc[-756:].min()) if len(df) >= 756 else l_2y
            
            m1 = ((cp - h_1y) / h_1y) * 100
            m2 = ((cp - h_2y) / h_2y) * 100
            m3 = ((cp - h_3y) / h_3y) * 100
            
            g1 = ((cp - l_1y) / l_1y) * 100
            g2 = ((cp - l_2y) / l_2y) * 100
            g3 = ((cp - l_3y) / l_3y) * 100
            
            # 🔥적극매수 -> 🟢매수 -> 🟡진입 순 정렬을 위한 점수 부여
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
        # 1. 적극매수 -> 매수 -> 진입 순으로 완벽 정렬
        results.sort(key=lambda x: x['Score'], reverse=True)
        
        # 2. 메시지 하나로 통합 (점선을 빼고 엔터로 구분하여 글자 수 제한 통과)
        msg = f"<b>🚀 통합 ETF 리포트</b>\n기준: {current_ny_time}\n\n"
        
        for row in results:
            msg += f"<b>{row['ETF']}</b> (${row['Price']}) {row['Status']}\n"
            msg += f"🔻MDD: 1년 {row['M1']}% | 2년 {row['M2']}% | 3년 {row['M3']}%\n"
            msg += f"🔺Gain: 1년 +{row['G1']}% | 2년 +{row['G2']}% | 3년 +{row['G3']}%\n\n"
        
        # 텔레그램 제한을 넘지 않도록 안전장치 후 전송
        if len(msg) > 4000:
            send_telegram_message(msg[:4000] + "\n... (글자 수 제한으로 생략됨)")
        else:
            send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send()
