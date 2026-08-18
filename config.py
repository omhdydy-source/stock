import os

# 실계좌 및 API 설정 (보안 강화: 하드코딩 제거 및 환경변수 필수화)
NHPLUG_APP_KEY = os.getenv("NHPLUG_APP_KEY")
NHPLUG_APP_SECRET = os.getenv("NHPLUG_APP_SECRET")
NHPLUG_BASE_URL = os.getenv("NHPLUG_BASE_URL", "https://api.nhplug.com:8443")
ACCOUNT_NO = os.getenv("ACCOUNT_NO", "20601669894")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 모니터링 대상 유니버스 (내 보유 종목 + 벤치마크)
PORTFOLIO_TICKERS = ["SOXL", "IQQ", "TQQQ"]
BENCHMARK_TICKERS = ["QQQ", "^VIX"]
