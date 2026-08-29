import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from data_collector import fetch_live_account, get_access_token
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO

def check_existing_reserved_orders():
    """
    NH투자증권 API를 통해 현재 계좌에 살아있는 미체결 예약 주문(미체결 내역)이 있는지 조회합니다.
    주문이 1개라도 남아있으면 True, 비어있으면 False를 반환합니다.
    """
    token = get_access_token()
    if not token:
        print("⚠️ 인증 토큰 발급 실패로 예약 주문 조회를 건너뜁니다.")
        return False

    url = f"{NHPLUG_BASE_URL}/gbstock/inquiry/v1/reservedOrderList"
    payload = {
        "Input_0": {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200"
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
            # Output_1 또는 응답 리스트에 미체결 예약 주문이 있는지 확인
            output_1 = res_data.get("Output_1", [])
            if output_1 and len(output_1) > 0:
                print(f"🔍 [계좌 검사] 현재 계좌에 미체결 예약 주문이 {len(output_1)}건 남아있습니다.")
                return True
            else:
                print("🔍 [계좌 검사] 현재 계좌에 남아있는 예약 주문이 없습니다. (그물망 비어있음)")
                return False
    except Exception as e:
        print(f"⚠️ 예약 주문 조회 중 오류 발생 (무시하고 진행): {e}")
        return False
