import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from data_collector import fetch_live_account, get_access_token
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO

def check_existing_reserved_orders():
    """
    NH투자증권 API를 통해 현재 계좌에 살아있는 해외주식 예약 주문이 있는지 조회합니다.
    주문이 1개라도 남아있으면 True, 비어있으면 False를 반환합니다.
    """
    token = get_access_token()
    if not token:
        print("⚠️ 인증 토큰 발급 실패로 예약 주문 조회를 건너뜁니다.")
        return False

    url = f"{NHPLUG_BASE_URL}/gbstock/inquiry/v1/reservedInquiry"
    today_str = datetime.now().strftime("%Y%m%d")
    payload = {
        "Input_0": {
            "fc_mkt_dit_cd": "200", # 미국
            "bkg_orr_dt": today_str,
            "act_no": ACCOUNT_NO,
            "sby_dit_cd": "0", # 전체
            "bkg_orr_can_yn": "0", # 전체
            "oss_orr_knd_cd": "0",
            "bkg_orr_tp_cd": "0",
            "wtm_cur_knd_cd": "0"
        }
    }
    req_data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers={
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": NHPLUG_APP_KEY,
        "appsecret": NHPLUG_APP_SECRET
    }, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            items = res_data.get("Output_1") or res_data.get("Output_0") or []
            if isinstance(items, list) and len(items) > 0:
                print(f"🔍 [계좌 검사] 현재 계좌에 예약 주문이 {len(items)}건 존재합니다.")
                return True
            else:
                print("🔍 [계좌 검사] 현재 계좌에 남아있는 예약 주문이 없습니다. (그물망 비어있음)")
                return False
    except Exception as e:
        print(f"⚠️ 예약 주문 조회 중 오류 발생 (무시하고 진행): {e}")
        return False
