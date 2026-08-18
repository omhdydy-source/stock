import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data, get_access_token
from quant_engine import load_state, save_state, get_current_price
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO

def send_live_order(operation_id, payload_input):
    token = get_access_token()
    if not token:
        print("❌ 인증 토큰 발급 실패로 주문을 전송할 수 없습니다.")
        return None

    # operation_id에 따른 엔드포인트 매핑
    endpoint_map = {
        "gbstockOrderBuy": "/gbstock/order/v1/buy",
        "gbstockOrderSell": "/gbstock/order/v1/sell"
    }
    
    path = endpoint_map.get(operation_id)
    if not path:
        print(f"❌ 알 수 없는 주문 operationId: {operation_id}")
        return None

    url = f"{NHPLUG_BASE_URL}{path}"
    full_payload = {"Input_0": payload_input}
    req_data = json.dumps(full_payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers={
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": NHPLUG_APP_KEY,
        "appsecret": NHPLUG_APP_SECRET
    }, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data
    except Exception as e:
        print(f"❌ 주문 API 전송 오류 ({operation_id}): {e}")
        return {"error": str(e)}

def execute_trading_pipeline(live_execute=False):
    print("🎯 [라오어 무한매수법 통합 주문 실행기 가동]")
    state = load_state()
    account_data = fetch_live_account()
    
    cash_usd = 0.0
    holdings = []
    if account_data and "Output_0" in account_data:
        summary = account_data["Output_0"]
        cash_usd = float(summary.get("fc_aet_amt", 0))

    if account_data and "Output_1" in account_data:
        holdings = account_data["Output_1"]

    curr_soxl = get_current_price("SOXL", 151.0)
    curr_tqqq = get_current_price("TQQQ", 76.0)

    orders_to_place = []

    print(f"\n[계좌 상태 요약]")
    print(f"- 가용 현금: ${cash_usd:,.2f}")

    # 1. 보유 종목 익절(매도) 조건 확인
    for h in holdings:
        code = h.get("iem_cd")
        qty = float(h.get("cns_bse_bnc_qty", 0))
        avg_p = float(h.get("fc_phs_uit_pr", 0))
        cur_p = float(h.get("fc_sec_end_pr", 0))
        pft = float(h.get("eal_pft_rt", 0))

        target_pct = 20.0 if code == "SOXL" else 10.0
        target_price = avg_p * (1.0 + target_pct / 100.0) if avg_p > 0 else 0.0

        print(f"• 종목: {code} | 수량: {qty}주 | 평단: ${avg_p:.2f} | 현재가: ${cur_p:.2f} | 수익률: {pft:+.2f}% (목표: +{target_pct}%, 목표가: ${target_price:.2f})")

        if qty > 0 and pft >= target_pct:
            print(f"🎉 [{code}] 목표 수익률 +{target_pct}% 달성! 익절 지정가 매도 주문 추가")
            sell_input = {
                "act_no": ACCOUNT_NO,
                "fc_sec_trd_nat_cd": "200",
                "iem_cd": code,
                "orr_qty": int(qty),
                "fc_orr_uit_pr": round(target_price, 2),
                "ahi_nmn_pr_tp_cd": "00"
            }
            orders_to_place.append(("gbstockOrderSell", sell_input))

    # 2. 신규 매수 (LOC) 조건 확인
    soxl_rem = max(1, 40 - state["SOXL"]["tranche"] + 1)
    tqqq_rem = max(1, 40 - state["TQQQ"]["tranche"] + 1)
    
    soxl_budget = min((cash_usd / 2) / soxl_rem, 500.0)
    tqqq_budget = min((cash_usd / 2) / tqqq_rem, 500.0)

    soxl_shares = int(soxl_budget / curr_soxl) if curr_soxl > 0 else 0
    if soxl_shares < 1 and cash_usd >= curr_soxl: soxl_shares = 1

    tqqq_shares = int(tqqq_budget / curr_tqqq) if curr_tqqq > 0 else 0
    if tqqq_shares < 1 and cash_usd >= curr_tqqq: tqqq_shares = 1

    if soxl_shares > 0:
        soxl_buy_input = {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200",
            "iem_cd": "SOXL",
            "orr_qty": soxl_shares,
            "fc_orr_uit_pr": round(curr_soxl, 2),
            "ahi_nmn_pr_tp_cd": "12",
            "wtm_cur_knd_cd": "1"
        }
        orders_to_place.append(("gbstockOrderBuy", soxl_buy_input))

    if tqqq_shares > 0:
        tqqq_buy_input = {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200",
            "iem_cd": "TQQQ",
            "orr_qty": tqqq_shares,
            "fc_orr_uit_pr": round(curr_tqqq, 2),
            "ahi_nmn_pr_tp_cd": "12",
            "wtm_cur_knd_cd": "1"
        }
        orders_to_place.append(("gbstockOrderBuy", tqqq_buy_input))

    print(f"\n[실행할 주문 리스트 ({len(orders_to_place)}건)]")
    for idx, (op_id, inp) in enumerate(orders_to_place, 1):
        print(f"--- 주문 #{idx} ({op_id}) ---")
        print(json.dumps(inp, indent=2, ensure_ascii=False))

        if live_execute:
            print(f"🚀 실계좌 주문 전송 중...")
            res = send_live_order(op_id, inp)
            print(f"📥 주문 결과 응답: {json.dumps(res, indent=2, ensure_ascii=False)}")
        else:
            print(f"💡 (드라이프런 모드 - 실제 전송하려면 --execute 플래그를 붙이세요)")

    return orders_to_place

if __name__ == "__main__":
    live = "--execute" in sys.argv
    execute_trading_pipeline(live_execute=live)
