import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

NHPLUG_APP_KEY = (os.getenv("NHPLUG_APP_KEY") or "").strip()
NHPLUG_APP_SECRET = (os.getenv("NHPLUG_APP_SECRET") or "").strip()
NHPLUG_BASE_URL = (os.getenv("NHPLUG_BASE_URL") or "https://api.nhplug.com:8443").strip()
ACCOUNT_NO = (os.getenv("ACCOUNT_NO") or "").strip()

TELEGRAM_TOKEN = (os.getenv("TELEGRAM_TOKEN") or "").strip()
CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()

PORTFOLIO_TICKERS = ["SOXL", "IQQ", "TQQQ"]
BENCHMARK_TICKERS = ["QQQ", "^VIX"]
