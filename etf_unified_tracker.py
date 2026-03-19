import requests
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def test_connection():
    text = "🔔 테스트 메시지: GitHub 연결에 성공했습니다!"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    
    response = requests.post(url, data=payload)
    print(f"상태 코드: {response.status_code}")
    print(f"응답 내용: {response.text}")

if __name__ == "__main__":
    test_connection()
