import os
import sys
import json
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data
from quant_engine import load_state, save_state, get_current_price

def calculate_loc_orders():
    print("🎯 [라오어 무한매수법 LOC 주문 계산기 가동]")
    state = load_state()
    account_data = fetch_live_account()
    
    cash_usd = 0.0
    if account_data and "Output_0" in account_data:
        summary = account_data["Output_0"]
        cash_usd = float(summary.get("fc_aet_amt", 0))

    curr_soxl = get_current_price("SOXL", 151.0)
    curr_tqqq = get_current_price("TQQQ", 76.0)

    remaining_tranches = max(1, state["total_tranches"] - state["tranche"] + 1)
    tranche_budget = min(cash_usd / remaining_tranches, 1000.0)
    half_budget = tranche_budget / 2.0

    soxl_shares = int(half_budget / curr_soxl) if curr_soxl > 0 else 0
    if soxl_shares < 1 and cash_usd >= curr_soxl:
        soxl_shares = 1

    tqqq_shares = int(half_budget / curr_tqqq) if curr_tqqq > 0 else 0
    if tqqq_shares < 1 and cash_usd >= curr_tqqq:
        tqqq_shares = 1

    print(f"\n[계좌 상태]")
    print(f"- 가용 현금: ${cash_usd:,.2f}")
    print(f"- 현재 회차: {state['tranche']}회차 / 총 {state['total_tranches']}회차 (사이클 #{state['cycle']})")
    print(f"- SOXL 현재가: ${curr_soxl:.2f} | 매수 수량: {soxl_shares}주 (예산: ${soxl_shares * curr_soxl:,.2f})")
    print(f"- TQQQ 현재가: ${curr_tqqq:.2f} | 매수 수량: {tqqq_shares}주 (예산: ${tqqq_shares * curr_tqqq:,.2f})")

    # LOC Order Payload Structure for NH Open API (gbstockOrderBuy)
    # ahi_nmn_pr_tp_cd: "12" (LOC 장마감 지정가)
    account_no = "20601669894"
    
    soxl_order = {
        "act_no": account_no,
        "fc_sec_trd_nat_cd": "200", # 미국
        "iem_cd": "SOXL",
        "orr_qty": soxl_shares,
        "fc_orr_uit_pr": round(curr_soxl, 2),
        "ahi_nmn_pr_tp_cd": "12", # LOC (장마감 지정가)
        "wtm_cur_knd_cd": "1" # 해당통화 (USD)
    }

    tqqq_order = {
        "act_no": account_no,
        "fc_sec_trd_nat_cd": "200", # 미국
        "iem_cd": "TQQQ",
        "orr_qty": tqqq_shares,
        "fc_orr_uit_pr": round(curr_tqqq, 2),
        "ahi_nmn_pr_tp_cd": "12", # LOC (장마감 지정가)
        "wtm_cur_knd_cd": "1" # 해당통화 (USD)
    }

    print("\n[생성된 LOC 주문 페이로드 (장마감 지정가)]")
    print("SOXL LOC 주문:", json.dumps(soxl_order, indent=2, ensure_ascii=False))
    print("TQQQ LOC 주문:", json.dumps(tqqq_order, indent=2, ensure_ascii=False))

    return {
        "soxl_order": soxl_order,
        "tqqq_order": tqqq_order,
        "state": state
    }

if __name__ == "__main__":
    calculate_loc_orders()
