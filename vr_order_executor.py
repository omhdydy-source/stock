import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from data_collector import fetch_live_account, get_access_token
from vr_engine import calculate_vr_cycle
from vr_bot import update_excel_log
from order_checker import check_existing_reserved_orders
from config import NHPLUG_APP_KEY, NHPLUG_APP_SECRET, NHPLUG_BASE_URL, ACCOUNT_NO, TELEGRAM_TOKEN, CHAT_ID

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def format_rich_telegram_report(rep, success_count, total_count):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_str = "거치식 (Lump-Sum)" if rep.get("mode") == "lump_sum" else "적립식"
    
    cycle_num = rep.get("cycle", 1)
    day_count = rep.get("day_count", 1)
    
    msg = f"📊 *[실계좌 VR 5.0 2주 주기 운용 리포트]*\n"
    msg += f"📅 일시: {now_str}\n"
    msg += f"⚙️ 운용 방식: {mode_str}\n"
    msg += f"🔄 운용 회차: 제 {cycle_num}회차 ({day_count}/14일차)\n"
    msg += f"──────────────────\n\n"
    msg += f"· TQQQ 보유 평단: `${rep['tqqq_avg_p']:,.2f}`\n"
    msg += f"· TQQQ 보유 개수: `{rep['tqqq_qty']:,.0f}주`\n"
    msg += f"· 총 주식 평가금: `${rep['total_stock_eval']:,.2f}`\n"
    msg += f"· 예수금 (Pool): `${rep['current_Pool']:,.2f}`\n"
    msg += f"· 총 자산: `${rep['total_asset']:,.2f}`\n\n"
    msg += f"· 적용 G값: `/{int(rep['G_value'])}` (기본 상승률: `{rep['basic_rate']:.2f}%`)\n"
    msg += f"· 새로운 목표선 (Next V): `${rep['next_V']:,.2f}`\n"
    msg += f"· 안전 밴드: `${rep['v_min']:,.2f} ~ ${rep['v_max']:,.2f}`\n\n"
    msg += f"💡 진단 결과: 【 `{rep['action']}` 】\n"
    msg += f"💬 설명: {rep['reason']}\n\n"
    msg += f"🟢 *[매수 30단계 예약 가이드 (주가 하락 시)]*:\n"
    for t in rep["buy_tier_orders"][:10]:
        msg += f"- {t['tier']}회차: 주가 `${t['price']:,.2f}` 도달 시 → {t['shares']}주 매수 (약 `${t['cost']:,.2f}` 소요)\n"
    msg += f"(외 20단계 생략... 총 30분할 적용 완료)\n\n"
    msg += f"🔴 *[매도 30단계 예약 가이드 (주가 상승 시)]*:\n"
    for t in rep["sell_tier_orders"][:10]:
        msg += f"- {t['tier']}회차: 주가 `${t['price']:,.2f}` 도달 시 → {t['shares']}주 매도 (약 `${t['revenue']:,.2f}` 익절)\n"
    msg += f"(외 20단계 생략... 총 30분할 적용 완료)\n\n"
    msg += f"✅ *예약 주문 전송 완료 (성공: {success_count}/{total_count})*"
    return msg

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
    print(f"📤 전송 페이로드: {json.dumps(full_payload, indent=2, ensure_ascii=False)}")
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

def execute_vr_orders(live_execute=False):
    print("🚀 [실계좌 VR 5.0 그물망 실행기 가동]")

    rep = calculate_vr_cycle()
    
    update_excel_log(rep)
    
    today_dt = datetime.now()
    end_dt = today_dt + timedelta(days=14)
    today_str = today_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")
    
    orders_to_place = []
    
    for t in rep["buy_tier_orders"]:
        buy_input = {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200",
            "iem_cd": "TQQQ",
            "oss_sby_dit_cd": "2",
            "orr_qty": t["shares"],
            "fc_orr_uit_pr": t["price"],
            "nmn_pr_tp_cd": "12",
            "bkg_orr_tp_cd": "2",
            "bkg_orr_sta_dt": today_str,
            "bkg_orr_end_dt": end_str,
            "wtm_cur_knd_cd": "1"
        }
        orders_to_place.append(("gbstockOrderReservedSubmit", buy_input))

    for t in rep["sell_tier_orders"]:
        sell_input = {
            "act_no": ACCOUNT_NO,
            "fc_sec_trd_nat_cd": "200",
            "iem_cd": "TQQQ",
            "oss_sby_dit_cd": "1",
            "orr_qty": t["shares"],
            "fc_orr_uit_pr": t["price"],
            "nmn_pr_tp_cd": "01",
            "bkg_orr_tp_cd": "2",
            "bkg_orr_sta_dt": today_str,
            "bkg_orr_end_dt": end_str,
            "wtm_cur_knd_cd": "1"
        }
        orders_to_place.append(("gbstockOrderReservedSubmit", sell_input))

    print(f"\n[생성된 VR 30분할 매수/매도 2주 예약 주문 총 {len(orders_to_place)}건]")

    success_count = 0
    if live_execute and orders_to_place:
        print(f"🚀 실계좌로 2주 유효기간 예약 주문 전송 중...")
        for op_id, inp in orders_to_place:
            res = send_live_order(op_id, inp)
            print(f"📥 주문 결과 응답: {json.dumps(res, indent=2, ensure_ascii=False)}")
            if res and res.get("rsp_cd") == "00162":
                success_count += 1
            time.sleep(0.3)
        print(f"✅ 모든 VR 예약 주문 전송 완료! (성공: {success_count}/{len(orders_to_place)})")
    else:
        print(f"💡 (드라이프런 모드)")

    rich_msg = format_rich_telegram_report(rep, success_count, len(orders_to_place))
    send_telegram_message(rich_msg)

    return orders_to_place

if __name__ == "__main__":
    import sys
    live = "--execute" in sys.argv
    execute_vr_orders(live_execute=live)
