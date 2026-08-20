import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data, get_access_token
from quant_engine import load_state, save_state, get_current_price, calculate_v4_params
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO

def send_live_order(operation_id, payload_input):
    token = get_access_token()
    if not token:
        print("❌ 인증 토큰 발급 실패로 주문을 전송할 수 없습니다.")
        return None

    endpoint_map = {
        "gbstockOrderBuy": "/gbstock/order/v1/buy",
        "gbstockOrderSell": "/gbstock/order/v1/sell",
        "gbstockOrderReservedSubmit": "/gbstock/order/v1/reservedSubmit"
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

def execute_v4_trading_pipeline(live_execute=False):
    print("🎯 [라오어 무한매수법 V4.0 예약/통합 주문 실행기 가동]")
    state = load_state()
    account_data = fetch_live_account()
    
    cash_usd = 0.0
    holdings = {}
    if account_data and "Output_0" in account_data:
        summary = account_data["Output_0"]
        cash_usd = float(summary.get("fc_aet_amt", 0))

    if account_data and "Output_1" in account_data:
        for h in account_data["Output_1"]:
            code = h.get("iem_cd")
            holdings[code] = {
                "qty": float(h.get("cns_bse_bnc_qty", 0)),
                "avg_p": float(h.get("fc_phs_uit_pr", 0)),
                "cur_p": float(h.get("fc_sec_end_pr", 0)),
                "pft": float(h.get("eal_pft_rt", 0))
            }

    curr_soxl = get_current_price("SOXL", 151.0)
    curr_tqqq = get_current_price("TQQQ", 76.0)

    orders_to_place = []
    t_deltas = {}
    today_str = datetime.now().strftime("%Y%m%d")

    # 🛡️ 중복 실행 방지 가드 제거 (사용자 요청에 따라 테스트를 위해 상시 허용)

    print(f"\n[계좌 상태 요약]")
    print(f"- 가용 현금: ${cash_usd:,.2f}\n")

    # 1. 매도(익절) 예약 주문 생성 로직 (V4.0: 쿼터매도 25% @ 별지점 LOC + 최종 지정가 매도 75% @ +20%/+15%)
    for code in ["SOXL", "TQQQ"]:
        if code in holdings:
            info = holdings[code]
            qty = int(info["qty"])
            avg_p = info["avg_p"]
            t_val = state.get(code, {}).get("T", 0.0)
            
            v4 = calculate_v4_params(code, avg_p, t_val, cash_usd / 2)
            star_price = v4["star_point"]
            target_price = v4["take_profit_price"]
            target_pct = v4["take_profit_pct"]

            if qty > 0:
                quarter_qty = int(qty * 0.25) if qty >= 4 else 0
                main_qty = qty - quarter_qty

                # 1-A. 쿼터매도 (25% 수량 @ 별지점 LOC 매도)
                if quarter_qty > 0:
                    print(f"🎯 [{code}] V4.0 쿼터매도(25%) 예약 주문 생성: {quarter_qty}주 @ 별지점 ${star_price:.2f} (LOC)")
                    q_sell_input = {
                        "act_no": ACCOUNT_NO,
                        "fc_sec_trd_nat_cd": "200",
                        "iem_cd": code,
                        "oss_sby_dit_cd": "1", # 1.매도
                        "orr_qty": quarter_qty,
                        "fc_orr_uit_pr": round(star_price, 2),
                        "nmn_pr_tp_cd": "12",  # 12. LOC (장마감 지정가)
                        "bkg_orr_tp_cd": "1",  # 1.일반예약
                        "bkg_orr_sta_dt": today_str,
                        "wtm_cur_knd_cd": "1"
                    }
                    orders_to_place.append(("gbstockOrderReservedSubmit", q_sell_input))

                # 1-B. 최종 지정가 매도 (75% 또는 전체 수량 @ +20%/+15%)
                if main_qty > 0:
                    print(f"🎯 [{code}] V4.0 최종 지정가 매도({75 if quarter_qty > 0 else 100}%) 예약 주문 생성: {main_qty}주 @ ${target_price:.2f} (+{target_pct}%)")
                    m_sell_input = {
                        "act_no": ACCOUNT_NO,
                        "fc_sec_trd_nat_cd": "200",
                        "iem_cd": code,
                        "oss_sby_dit_cd": "1", # 1.매도
                        "orr_qty": main_qty,
                        "fc_orr_uit_pr": round(target_price, 2),
                        "nmn_pr_tp_cd": "00",  # 00. 지정가
                        "bkg_orr_tp_cd": "1",  # 1.일반예약
                        "bkg_orr_sta_dt": today_str,
                        "wtm_cur_knd_cd": "1"
                    }
                    orders_to_place.append(("gbstockOrderReservedSubmit", m_sell_input))

    # 2. 매수 (V4.0 별지점 + 큰수 매수 버퍼) 예약 주문 생성 로직
    for code in ["SOXL", "TQQQ"]:
        t_val = state[code]["T"]
        avg_p = holdings.get(code, {}).get("avg_p", curr_soxl if code=="SOXL" else curr_tqqq)
        cur_price = curr_soxl if code == "SOXL" else curr_tqqq
        
        v4 = calculate_v4_params(code, avg_p, t_val, cash_usd / 2)
        buy_price = v4["buy_point"]
        
        # 큰수 매수 버퍼 반영
        if t_val == 0.0:
            buy_price = round(cur_price * 1.12, 2)

        # V4.0 수량 조절 배수
        ratio = cur_price / avg_p if avg_p > 0 else 1.0
        mult = 0.5 if ratio >= 1.05 else (2.0 if ratio <= 0.95 else 1.0)
        base_shares = int(v4["daily_budget"] / cur_price) if cur_price > 0 else 1
        shares = int(base_shares * mult)
        if shares < 1: shares = 1

        t_deltas[code] = mult
        buy_input = {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200",
            "iem_cd": code,
            "oss_sby_dit_cd": "2", # 2.매수
            "orr_qty": shares,
            "fc_orr_uit_pr": round(buy_price, 2),
            "nmn_pr_tp_cd": "12",  # 12. LOC (장마감 지정가)
            "bkg_orr_tp_cd": "1",  # 1.일반예약
            "bkg_orr_sta_dt": today_str,
            "wtm_cur_knd_cd": "1"
        }
        orders_to_place.append(("gbstockOrderReservedSubmit", buy_input))
        print(f"• [{code} V4.0 예약 매수 가이드]: 회차 T={t_val:.1f} | 매수가(별지점): ${buy_price:.2f} | 수량: {shares}주 (LOC 예약)")

    print(f"\n[실행할 V4.0 예약 주문 리스트 ({len(orders_to_place)}건)]")
    for idx, (op_id, inp) in enumerate(orders_to_place, 1):
        print(f"--- 주문 #{idx} ({op_id}) ---")
        print(json.dumps(inp, indent=2, ensure_ascii=False))

        if live_execute:
            print(f"🚀 실계좌 V4.0 예약 주문 전송 중...")
            res = send_live_order(op_id, inp)
            print(f"📥 주문 결과 응답: {json.dumps(res, indent=2, ensure_ascii=False)}")
            time.sleep(1.5)
        else:
            print(f"💡 (드라이프런 모드 - 실제 전송하려면 --execute 플래그를 붙이세요)")

    if live_execute and orders_to_place:
        state["last_order_date"] = today_str
        # 🔄 V4.0 회차(T) 자동 증가 반영 (주문 발송 시 매수 배수만큼 T값 업데이트)
        for code, t_delta in t_deltas.items():
            old_t = state.get(code, {}).get("T", 0.0)
            new_t = old_t + t_delta
            if code in state:
                state[code]["T"] = round(new_t, 2)
            print(f"📈 [{code}] 회차(T값) 업데이트: T={old_t:.1f} ➔ T={state[code]['T']:.1f} (+{t_delta} 반영)")

        save_state(state)
        print(f"🔒 [중복 방지 & 상태 업데이트] 상태 파일에 오늘 날짜({today_str}) 및 T값 저장 완료.")

    return orders_to_place

if __name__ == "__main__":
    live = "--execute" in sys.argv
    execute_v4_trading_pipeline(live_execute=live)
