import os
import json
import yfinance as yf
from datetime import datetime, timedelta
from data_collector import fetch_live_account

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VR_STATE_FILE = os.path.join(BASE_DIR, "vr_state.json")

def get_current_price(ticker_symbol, default_fallback=100.0):
    try:
        tk = yf.Ticker(ticker_symbol)
        p = getattr(tk.fast_info, "last_price", None)
        if p and p > 0:
            return float(p)
        df = tk.history(period="5d")
        if not df.empty:
            df = df.dropna(subset=["Close"])
            if not df.empty:
                return float(df["Close"].iloc[-1])
    except Exception:
        pass
    return default_fallback

def load_vr_state():
    default_state = {
        "ticker": "PORTFOLIO_TOTAL",
        "cycle": 1,
        "V": 0.0,
        "Pool": 0.0,
        "G": 10.0,
        "mode": "lump_sum",
        "deposit_amount": 0.0,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "last_cycle_date": datetime.now().strftime("%Y-%m-%d"),
        "last_update_year": datetime.now().year,
        "history": []
    }
    if os.path.exists(VR_STATE_FILE):
        try:
            with open(VR_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_state.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return default_state

def save_vr_state(state):
    try:
        with open(VR_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"VR 상태 저장 오류: {e}")

def calculate_vr_cycle(deposit=None, withdrawal=0.0):
    state = load_vr_state()
    acc = fetch_live_account()
    
    cash_usd = 0.0
    total_stock_eval = 0.0
    holdings_summary = []
    
    if acc and "Output_0" in acc:
        summary = acc["Output_0"]
        cash_usd = float(summary.get("fc_ny_stl_xcl_amt", 0.0))
        if cash_usd <= 0.0:
            total_aet = float(summary.get("fc_aet_amt", 0.0))
            total_eal = float(summary.get("fc_eal_amt", 0.0))
            cash_usd = max(0.0, total_aet - total_eal)
        
    if acc and "Output_1" in acc:
        for h in acc["Output_1"]:
            code = h.get("iem_cd")
            qty = float(h.get("cns_bse_bnc_qty", 0.0))
            eval_amt = float(h.get("fc_eal_amt", 0.0))
            avg_p = float(h.get("fc_phs_uit_pr", 0.0))
            cur_p = float(h.get("fc_sec_end_pr", 0.0))
            total_stock_eval += eval_amt
            holdings_summary.append({
                "code": code,
                "qty": qty,
                "eval_amt": eval_amt,
                "avg_p": avg_p,
                "cur_p": cur_p
            })

    # API 조회 실패 시 상태 파일(state["Pool"]) 변수를 폴백으로 사용
    if total_stock_eval == 0.0 and cash_usd == 0.0:
        total_stock_eval = float(state.get("V", 18423.45))
        cash_usd = float(state.get("Pool", 5000.0))
        holdings_summary = [
            {"code": "TQQQ", "qty": 200.0, "eval_amt": total_stock_eval * 0.7, "avg_p": 70.87, "cur_p": 71.68}
        ]
    elif cash_usd > 0.0:
        state["Pool"] = cash_usd
        save_vr_state(state)

    # TQQQ 평단 및 개수 추출
    tqqq_qty = 0.0
    tqqq_avg_p = 0.0
    ref_price = 71.68
    for h in holdings_summary:
        if h["code"] == "TQQQ":
            tqqq_qty = h["qty"]
            tqqq_avg_p = h["avg_p"]
            if h["cur_p"] > 0:
                ref_price = h["cur_p"]

    if state["V"] <= 0.0:
        state["V"] = total_stock_eval if total_stock_eval > 0 else 18423.45
        state["Pool"] = cash_usd
        state["G"] = 10.0
        state["last_cycle_date"] = datetime.now().strftime("%Y-%m-%d")
        save_vr_state(state)

    current_year = datetime.now().year
    last_year = state.get("last_update_year", current_year)
    if current_year > last_year:
        years_passed = current_year - last_year
        state["G"] += years_passed
        state["last_update_year"] = current_year
        save_vr_state(state)

    G = state["G"]
    V = state["V"]
    Pool = cash_usd
    
    mode = state.get("mode", "lump_sum")
    if mode == "lump_sum":
        deposit = 0.0
    else:
        if deposit is None:
            deposit = state.get("deposit_amount", 0.0)
            
    pool_ratio = (Pool / V) if V > 0 else 0.0
    basic_rate = pool_ratio / G
    add_rate = 0.005 if total_stock_eval > V else 0.0
    total_rate = basic_rate + add_rate
    
    next_V = V * (1.0 + total_rate) + deposit - withdrawal
    v_min = next_V * 0.80
    v_max = next_V * 1.25
    
    today_dt = datetime.now()
    last_cycle_dt = datetime.strptime(state.get("last_cycle_date", today_dt.strftime("%Y-%m-%d")), "%Y-%m-%d")
    days_passed = (today_dt - last_cycle_dt).days
    day_count = min(14, max(1, days_passed + 1))
    
    cycle_updated = False
    if days_passed >= 14:
        state["V"] = next_V
        state["cycle"] += 1
        state["last_cycle_date"] = today_dt.strftime("%Y-%m-%d")
        days_passed = 0
        day_count = 1
        cycle_updated = True
        save_vr_state(state)

    action = "HOLD"
    trade_amount = 0.0
    num_tiers = 30

    if total_stock_eval < v_min:
        action = "BUY"
        trade_amount = max(0.0, next_V - total_stock_eval)
        if trade_amount > Pool:
            trade_amount = Pool
        reason = f"주식 평가금이 하단선 아래로 이탈했습니다. 총 ${trade_amount:,.2f} 매수 필요."
    elif total_stock_eval > v_max:
        action = "SELL"
        trade_amount = max(0.0, total_stock_eval - next_V)
        reason = f"주식 평가금이 상단선 위로 이탈했습니다. 총 ${trade_amount:,.2f} 매도 필요."
    else:
        buy_deficit = max(0.0, next_V - total_stock_eval)
        sell_excess = max(0.0, total_stock_eval - next_V)
        trade_amount = buy_deficit if buy_deficit > 0 else sell_excess
        reason = f"안전 밴드 내 홀드 중 (하단 터치 시 매수 필요액: ${buy_deficit:,.2f} / 상단 터치 시 매도 초과액: ${sell_excess:,.2f})"

    # 매수 30단계 가이드
    buy_tier_orders = []
    budget_per_tier = Pool / num_tiers if Pool > 0 else 63.0
    v_min_share_price = max(1.0, (v_min / (total_stock_eval / ref_price))) if total_stock_eval > 0 else ref_price * 0.80
    price_step_down = max(0.05, (ref_price - v_min_share_price) / num_tiers)

    for i in range(1, num_tiers + 1):
        tier_price = ref_price - (price_step_down * i)
        if tier_price < 1.0: tier_price = 1.0
        tier_shares = int(budget_per_tier / tier_price) if tier_price > 0 else 1
        if tier_shares < 1: tier_shares = 1
        buy_tier_orders.append({
            "tier": i,
            "price": round(tier_price, 2),
            "shares": tier_shares,
            "cost": round(tier_price * tier_shares, 2)
        })

    # 매도 30단계 가이드
    sell_tier_orders = []
    shares_per_tier = max(1, int(tqqq_qty / num_tiers)) if tqqq_qty > 0 else 6
    v_max_share_price = (v_max / (total_stock_eval / ref_price)) if total_stock_eval > 0 else ref_price * 1.25
    price_step_up = max(0.05, (v_max_share_price - ref_price) / num_tiers)

    for i in range(1, num_tiers + 1):
        tier_price = ref_price + (price_step_up * i)
        sell_tier_orders.append({
            "tier": i,
            "price": round(tier_price, 2),
            "shares": shares_per_tier,
            "revenue": round(tier_price * shares_per_tier, 2)
        })

    state["Pool"] = Pool
    save_vr_state(state)

    report = {
        "ticker": "PORTFOLIO_TOTAL",
        "mode": mode,
        "deposit_amount": deposit,
        "total_stock_eval": total_stock_eval,
        "cash_usd": Pool,
        "total_asset": total_stock_eval + Pool,
        "tqqq_qty": tqqq_qty,
        "tqqq_avg_p": tqqq_avg_p,
        "holdings": holdings_summary,
        "current_V": V,
        "current_Pool": Pool,
        "G_value": G,
        "pool_ratio": pool_ratio * 100,
        "basic_rate": basic_rate * 100,
        "add_rate": add_rate * 100,
        "total_rate": total_rate * 100,
        "next_V": next_V,
        "v_min": v_min,
        "v_max": v_max,
        "action": action,
        "trade_amount": trade_amount,
        "daily_trade_amount": trade_amount / num_tiers,
        "buy_tier_orders": buy_tier_orders,
        "sell_tier_orders": sell_tier_orders,
        "cycle": state["cycle"],
        "day_count": day_count,
        "days_passed": days_passed,
        "cycle_updated": cycle_updated,
        "reason": reason
    }
    
    return report

if __name__ == "__main__":
    rep = calculate_vr_cycle()
    print("TQQQ 평단:", rep['tqqq_avg_p'], "개수:", rep['tqqq_qty'])
