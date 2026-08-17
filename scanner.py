import os
import urllib.request
import json
import yfinance as yf
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Error: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables must be set.")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            print("Telegram message sent successfully.")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

def check_market():
    print("Fetching QQQ and TQQQ data...")
    # QQQ data for 200 SMA check
    qqq = yf.download("QQQ", period="1y", interval="1d", progress=False)
    if qqq.empty:
        send_telegram("⚠️ [스윙봇 오류] QQQ 데이터를 가져오지 못했습니다.")
        return

    # Handle multi-index columns if returned by newer yfinance
    if hasattr(qqq.columns, 'levels'):
        qqq.columns = qqq.columns.get_level_values(0)

    close_prices = qqq['Close']
    current_price = float(close_prices.iloc[-1])
    
    # Calculate 200 SMA
    sma_200 = float(close_prices.rolling(window=200).mean().iloc[-1])
    
    # Determine signal
    is_above_200 = current_price > sma_200
    signal_text = "🟢 상승장 (TQQQ 보유 / 매수 가능)" if is_above_200 else "🔴 하락장 (현금 대피 / TQQQ 매도)"

    report = (
        f"📊 *TQQQ 스윙 트레이딩 & 200일선 방어 리포트*\n"
        f"📅 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"• QQQ 현재가: `${current_price:.2f}`\n"
        f"• QQQ 200일선: `${sma_200:.2f}`\n"
        f"• 판정 시그널: *{signal_text}*\n\n"
        f"💡 *투자 가이드*:\n"
        f"- 200일선 위에 있으면 TQQQ 적립식 매수 및 보유\n"
        f"- 200일선 아래로 내려가면 전량 현금화하여 하락장 방어"
    )

    print(report)
    send_telegram(report)

if __name__ == "__main__":
    check_market()
