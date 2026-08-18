import os
import sys
import json
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data
from quant_engine import load_state, save_state, get_current_price

def execute_trading_pipeline():
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

    account_no = "20601669894"
    orders_to_place = []

    print(f"\n[계좌 상태 요약]")
    print(f"- 가용 현금: ${cash_usd:,.2f}")

    # 1. 보유 종목 익절(매도) 조건 확인 및 매도 페이로드 생성
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
            print(f"🎉 [{code}] 목표 수익률 +{target_pct}% 달성! 익절 지정가 매도 주문 생성 중...")
            sell_order = {
                "operationId": "gbstockOrderSell",
                "input": {
                    "act_no": account_no,
                    "fc_sec_trd_nat_cd": "200",
                    "iem_cd": code,
                    "orr_qty": int(qty),
                    "fc_orr_uit_pr": round(target_price, 2),
                    "ahi_nmn_pr_tp_cd": "00" # 00.지정가 매도
                }
            }
            orders_to_place.append(sell_order)

    # 2. 신규 매수 (LOC) 조건 확인 및 매수 페이로드 생성
    soxl_rem = max(1, 40 - state["SOXL"]["tranche"] + 1)
    tqqq_rem = max(1, 40 - state["TQQQ"]["tranche"] + 1)
    
    soxl_budget = min((cash_usd / 2) / soxl_rem, 500.0)
    tqqq_budget = min((cash_usd / 2) / tqqq_rem, 500.0)

    soxl_shares = int(soxl_budget / curr_soxl) if curr_soxl > 0 else 0
    if soxl_shares < 1 and cash_usd >= curr_soxl: soxl_shares = 1

    tqqq_shares = int(tqqq_budget / curr_tqqq) if curr_tqqq > 0 else 0
    if tqqq_shares < 1 and cash_usd >= curr_tqqq: tqqq_shares = 1

    if soxl_shares > 0:
        soxl_buy_order = {
            "operationId": "gbstockOrderBuy",
            "input": {
                "act_no": account_no,
                "fc_sec_trd_nat_cd": "200",
                "iem_cd": "SOXL",
                "orr_qty": soxl_shares,
                "fc_orr_uit_pr": round(curr_soxl, 2),
                "ahi_nmn_pr_tp_cd": "12", # 12.LOC (장마감 지정가)
                "wtm_cur_knd_cd": "1"
            }
        }
        orders_to_place.append(soxl_buy_order)

    if tqqq_shares > 0:
        tqqq_buy_order = {
            "operationId": "gbstockOrderBuy",
            "input": {
                "act_no": account_no,
                "fc_sec_trd_nat_cd": "200",
                "iem_cd": "TQQQ",
                "orr_qty": tqqq_shares,
                "fc_orr_uit_pr": round(curr_tqqq, 2),
                "ahi_nmn_pr_tp_cd": "12", # 12.LOC (장마감 지정가)
                "wtm_cur_knd_cd": "1"
            }
        }
        orders_to_place.append(tqqq_buy_order)

    print(f"\n[생성된 최종 주문 페이로드 리스트 ({len(orders_to_place)}건)]")
    for idx, ord_item in enumerate(orders_to_place, 1):
        print(f"--- 주문 #{idx} ({ord_item['operationId']}) ---")
        print(json.dumps(ord_item['input'], indent=2, ensure_ascii=False))

    return orders_to_place

if __name__ == "__main__":
    execute_trading_pipeline()
