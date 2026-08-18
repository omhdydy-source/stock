import os
import urllib.request
import urllib.parse
import json
import yfinance as yf
import pandas as pd
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO, PORTFOLIO_TICKERS, BENCHMARK_TICKERS

def get_access_token():
    try:
        params = {
            "appkey": NHPLUG_APP_KEY,
            "appsecretkey": NHPLUG_APP_SECRET,
            "grant_type": "client_credentials",
            "scope": "oob"
        }
        url = f"{NHPLUG_BASE_URL}/oauth2/token?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, data=b"", headers={"content-type": "application/x-www-form-urlencoded"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("access_token")
    except Exception as e:
        print(f"토큰 발급 실패: {e}")
        return None

def fetch_live_account():
    token = get_access_token()
    if not token:
        return None
    try:
        bal_url = f"{NHPLUG_BASE_URL}/gbstock/inquiry/v1/balance"
        payload = {
            "Input_0": {
                "act_no": ACCOUNT_NO,
                "qut_iqr_dit_cd": "9",
                "fc_sec_trd_nat_cd": "200",
                "cur_cd": "USD"
            }
        }
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(bal_url, data=req_data, headers={
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": NHPLUG_APP_KEY,
            "appsecret": NHPLUG_APP_SECRET
        }, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"실계좌 조회 실패: {e}")
        return None

def fetch_fear_and_greed():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://edition.cnn.com/"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            score = float(data["fear_and_greed"]["score"])
            rating = str(data["fear_and_greed"]["rating"])
            return {"score": score, "rating": rating}
    except Exception as e:
        print(f"Fear & Greed 수집 오류: {e}")
        return None

def fetch_market_data():
    data = {}
    all_tickers = PORTFOLIO_TICKERS + BENCHMARK_TICKERS
    for t in all_tickers:
        try:
            df = yf.Ticker(t).history(period="1y")
            if not df.empty:
                data[t] = df
        except Exception as e:
            print(f"시장 데이터 수집 오류 ({t}): {e}")
    
    # Add Fear & Greed Index
    fn_g = fetch_fear_and_greed()
    if fn_g:
        data["FearAndGreed"] = fn_g

    return data
