import urllib.request
import json
from config import TELEGRAM_TOKEN, CHAT_ID
from data_collector import fetch_live_account, fetch_market_data
from quant_engine import analyze_portfolio
from excel_logger import log_portfolio_to_excel

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        print(text)
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_length = 3500
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    for idx, chunk in enumerate(chunks):
        # Plain text fallback if markdown fails
        data = json.dumps({"chat_id": CHAT_ID, "text": chunk}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"텔레그램 브리핑 전송 완료 (청크 {idx+1}/{len(chunks)})")
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

def main():
    print("🏛️ [모듈러 실계좌 퀀트 시스템] 데이터 수집 및 분석 가동...")
    
    # 1. Excel 로깅 수행
    try:
        log_portfolio_to_excel()
    except Exception as e:
        print(f"⚠️ 엑셀 로깅 중 오류 발생: {e}")

    # 2. 실계좌 및 시장 데이터 수집
    account_data = fetch_live_account()
    market_data = fetch_market_data()
    
    # 3. 포트폴리오 분석 및 리포트 생성
    report = analyze_portfolio(account_data, market_data)
    print("\n" + report + "\n")
    
    # 4. 텔레그램 전송
    send_telegram(report)
    print("✅ 모든 프로세스가 완료되었습니다!")

if __name__ == "__main__":
    main()
