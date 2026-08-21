import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "infinite_v4_state.json")

def load_state():
    state = {
        "SOXL": {"cycle": 1, "T": 0.0, "total_tranches": 40},
        "TQQQ": {"cycle": 1, "T": 0.0, "total_tranches": 40}
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "SOXL" in data and "TQQQ" in data:
                    state = data
        except Exception:
            pass

    # 🔗 선택적 엑셀 동기화 (파일 및 시트가 존재할 경우에만 조용히 반영)
    excel_path = os.path.join(BASE_DIR, "stock_portfolio_log.xlsx")
    if os.path.exists(excel_path):
        try:
            xl = pd.ExcelFile(excel_path)
            if "자산요약대시보드" in xl.sheet_names:
                df_sum = pd.read_excel(excel_path, sheet_name="자산요약대시보드")
                if not df_sum.empty:
                    last_row = df_sum.iloc[-1]
                    if "SOXL 사이클" in last_row and "SOXL T회차" in last_row:
                        state["SOXL"]["cycle"] = int(last_row["SOXL 사이클"])
                        state["SOXL"]["T"] = float(last_row["SOXL T회차"])
                    if "TQQQ 사이클" in last_row and "TQQQ T회차" in last_row:
                        state["TQQQ"]["cycle"] = int(last_row["TQQQ 사이클"])
                        state["TQQQ"]["T"] = float(last_row["TQQQ T회차"])
        except Exception:
            pass # 깃허브 액션스 등에서 엑셀이 없거나 잠겨있어도 JSON 상태로 안전하게 동작

    return state

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"상태 저장 오류: {e}")

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

def calculate_v4_params(ticker, avg_price, T, cash, total_tranches=40):
    # 1. 별% (Star %) 공식 (V4.0 오피셜)
    if ticker == "SOXL":
        star_pct = 20.0 - (1.0 * T)
    else: # TQQQ / IQQ 등
        star_pct = 15.0 - (0.75 * T)
        
    star_point = avg_price * (1.0 + star_pct / 100.0) if avg_price > 0 else 0.0
    buy_point = star_point - 0.01 if star_point > 0.01 else star_point
    
    # 2. 일일 매수금 공식: 잔금 / (총분할수 - T)
    remaining_tranches = max(0.1, total_tranches - T)
    daily_budget = cash / remaining_tranches if remaining_tranches > 0 else cash
    
    # 3. 최종 지정가 매도 목표 (V4.0 기준: SOXL +20%, TQQQ +15%)
    take_profit_pct = 20.0 if ticker == "SOXL" else 15.0
    take_profit_price = avg_price * (1.0 + take_profit_pct / 100.0) if avg_price > 0 else 0.0
    
    return {
        "star_pct": star_pct,
        "star_point": star_point,
        "buy_point": buy_point,
        "daily_budget": daily_budget,
        "take_profit_pct": take_profit_pct,
        "take_profit_price": take_profit_price
    }

def analyze_portfolio(account_data, market_data):
    state = load_state()
    
    total_asset_krw = 0
    total_asset_usd = 0
    cash_usd = 0
    tot_eval_usd = 0
    tot_profit_usd = 0
    tot_pft_rt = 0

    if account_data and "Output_0" in account_data:
        summary = account_data["Output_0"]
        total_asset_krw = float(summary.get("tot_aet_amt", 0))
        cash_usd = float(summary.get("fc_aet_amt", 0))
        tot_eval_usd = float(summary.get("fc_eal_amt", 0))
        total_asset_usd = cash_usd + tot_eval_usd
        tot_profit_usd = float(summary.get("fc_eal_pls_amt", 0))
        tot_pft_rt = float(summary.get("pft_rt", 0))

    holdings_dict = {}
    if account_data and "Output_1" in account_data:
        for h in account_data["Output_1"]:
            code = h.get("iem_cd")
            qty = float(h.get("cns_bse_bnc_qty", 0))
            avg_p = float(h.get("fc_phs_uit_pr", 0))
            cur_p = float(h.get("fc_sec_end_pr", 0))
            pft = float(h.get("eal_pft_rt", 0))
            
            holdings_dict[code] = {
                "qty": qty,
                "avg_p": avg_p,
                "cur_p": cur_p,
                "pft": pft
            }

    # 🔄 스마트 오토 리셋 (보유 수량이 0주인 경우 사이클 완료로 판정하여 리셋)
    state_updated = False
    for ticker in ["SOXL", "TQQQ"]:
        holding_qty = holdings_dict.get(ticker, {}).get("qty", 0.0)
        if holding_qty == 0 and state[ticker]["T"] > 0:
            print(f"🔄 [{ticker}] 보유 수량이 0주입니다. V4.0 익절 완료로 감지하여 사이클 #{state[ticker]['cycle'] + 1}, T=0으로 자동 리셋합니다!")
            state[ticker]["cycle"] += 1
            state[ticker]["T"] = 0.0
            state_updated = True

    if state_updated:
        save_state(state)

    report_lines = [
        "🎯 *[라오어 무한매수법 V4.0 오피셜 엔진 브리핑]*",
        f"📅 보고 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "💼 *1. 실계좌 보유 포지션 및 V4.0 회차(T) 현황*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"• **총 평가 자산**: `₩{total_asset_krw:,.0f}` (`${total_asset_usd:,.2f}`)",
        f"• **가용 현금 (예수금)**: `${cash_usd:,.2f}`",
        f"• **보유주식 평가금액**: `${tot_eval_usd:,.2f}`",
        f"• **전체 평가 손익**: `${tot_profit_usd:+,.2f}` (`{tot_pft_rt:+.2f}%`)",
        f"• **V4.0 종목별 회차(T) 및 사이클**:",
        f"  - SOXL: `T = {state['SOXL']['T']:.2f}` (사이클 #{state['SOXL']['cycle']} / 40분할)",
        f"  - TQQQ: `T = {state['TQQQ']['T']:.2f}` (사이클 #{state['TQQQ']['cycle']} / 40분할)\n"
    ]

    if holdings_dict:
        report_lines.append("📌 *보유 종목별 V4.0 파라미터 진단*:")
        for code in ["SOXL", "TQQQ", "IQQ"]:
            if code in holdings_dict:
                info = holdings_dict[code]
                t_val = state.get(code, {}).get("T", 0.0)
                v4 = calculate_v4_params(code, info["avg_p"], t_val, cash_usd)
                
                phase = "전반전" if t_val < 20 else "후반전"
                report_lines.append(f"  • *{code}* ({phase}, T={t_val:.1f}): `{info['qty']}주` | 평단: `${info['avg_p']:.2f}` | 현재가: `${info['cur_p']:.2f}`")
                report_lines.append(f"    - 수익률: `{info['pft']:+.2f}%` | 별지점: `${v4['star_point']:.2f}` (별%: `{v4['star_pct']:+.2f}%`)")
                report_lines.append(f"    - 1회 예산(잔금/(40-T)): `${v4['daily_budget']:.2f}` | 최종목표가: `${v4['take_profit_price']:.2f}` (+{v4['take_profit_pct']}%)")

    # Macro Trend Analysis
    report_lines.extend([
        "\n━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 *2. 거시 추세 및 무한매수 필터 진단*",
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    ])

    qqq_df = market_data.get("QQQ")
    vix_df = market_data.get("^VIX")
    fear_greed = market_data.get("FearAndGreed")

    curr_soxl = get_current_price("SOXL", 151.0)
    curr_tqqq = get_current_price("TQQQ", 76.0)

    is_bullish = True
    if qqq_df is not None and not qqq_df.empty:
        qqq_df = qqq_df.dropna(subset=["Close"])
        if not qqq_df.empty:
            curr_qqq = float(qqq_df["Close"].iloc[-1])
            sma_200 = float(qqq_df["Close"].rolling(window=200).mean().iloc[-1])
            is_bullish = curr_qqq > sma_200
            trend_str = "🟢 BULLISH (상승장 - 무한매수 정상 진행)" if is_bullish else "🔴 BEARISH (하락장 - 무한매수 일시정지 & 현금보존)"
            report_lines.append(f"• **나스닥(QQQ)**: `${curr_qqq:.2f}` (200일선: `${sma_200:.2f}`)")
            report_lines.append(f"• **거시 추세 판정**: *{trend_str}*")

    if vix_df is not None and not vix_df.empty:
        vix_df = vix_df.dropna(subset=["Close"])
        if not vix_df.empty:
            curr_vix = float(vix_df["Close"].iloc[-1])
            vix_status = "안정 (탐욕 구간 - 레버리지 유리)" if curr_vix < 20 else ("주의 (변동성 확대 - 비중 축소)" if curr_vix < 30 else "위험 경보 (패닉 장세 - 전량 현금 대피)")
            report_lines.append(f"• **공포지수 (VIX)**: `${curr_vix:.2f}` ({vix_status})")

    if fear_greed:
        score = fear_greed["score"]
        rating = fear_greed["rating"].upper()
        report_lines.append(f"• **공포·탐욕 지수 (Fear & Greed)**: `{score:.1f}` ({rating})")

    # V4.0 Execution Guide
    report_lines.extend([
        "\n━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 *3. 라오어 무한매수법 V4.0 오피셜 매수/매도 가이드*",
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    ])

    if is_bullish:
        soxl_info = holdings_dict.get("SOXL", {})
        tqqq_info = holdings_dict.get("TQQQ", {})

        curr_soxl = soxl_info.get("cur_p") or curr_soxl
        curr_tqqq = tqqq_info.get("cur_p") or curr_tqqq

        soxl_avg = soxl_info.get("avg_p", curr_soxl)
        soxl_qty = int(soxl_info.get("qty", 0))
        tqqq_avg = tqqq_info.get("avg_p", curr_tqqq)
        tqqq_qty = int(tqqq_info.get("qty", 0))

        soxl_v4 = calculate_v4_params("SOXL", soxl_avg, state["SOXL"]["T"], cash_usd / 2)
        tqqq_v4 = calculate_v4_params("TQQQ", tqqq_avg, state["TQQQ"]["T"], cash_usd / 2)

        soxl_q_qty = int(soxl_qty * 0.25) if soxl_qty >= 4 else 0
        soxl_m_qty = soxl_qty - soxl_q_qty

        tqqq_q_qty = int(tqqq_qty * 0.25) if tqqq_qty >= 4 else 0
        tqqq_m_qty = tqqq_qty - tqqq_q_qty

        # V4.0 수량 조절 배수 (Quantity Multiplier: 고가 절반매수 0.5x / 저가 더블매수 2.0x / 정규 1.0x)
        soxl_ratio = curr_soxl / soxl_avg if soxl_avg > 0 else 1.0
        soxl_mult = 0.5 if soxl_ratio >= 1.05 else (2.0 if soxl_ratio <= 0.95 else 1.0)
        soxl_base = int(soxl_v4["daily_budget"] / curr_soxl) if curr_soxl > 0 else 1
        soxl_shares = int(soxl_base * soxl_mult)
        if soxl_shares < 1: soxl_shares = 1

        tqqq_ratio = curr_tqqq / tqqq_avg if tqqq_avg > 0 else 1.0
        tqqq_mult = 0.5 if tqqq_ratio >= 1.05 else (2.0 if tqqq_ratio <= 0.95 else 1.0)
        tqqq_base = int(tqqq_v4["daily_budget"] / curr_tqqq) if curr_tqqq > 0 else 1
        tqqq_shares = int(tqqq_base * tqqq_mult)
        if tqqq_shares < 1: tqqq_shares = 1

        report_lines.append("• **V4.0 실행 모드**: *[오피셜 공식 적용 중 (수량 배수 조절 반영)]*")
        
        report_lines.append(s := f"\n👉 **[SOXL V4.0 가이드 (T={state['SOXL']['T']:.1f} 회차 / 사이클 #{state['SOXL']['cycle']})]**")
        report_lines.append(f"  - **별지점 LOC 매수**: `${soxl_v4['buy_point']:.2f}` (별% {soxl_v4['star_pct']:+.2f}%) | 수량: `{soxl_shares}주` (배수: `{soxl_mult}x`)")
        report_lines.append(f"  - **쿼터매도(25%)**: `{soxl_q_qty}주` @ 별지점 `${soxl_v4['star_point']:.2f}` (LOC)")
        report_lines.append(f"  - **최종지정가매도({75 if soxl_q_qty > 0 else 100}%)**: `{soxl_m_qty}주` @ `${soxl_v4['take_profit_price']:.2f}` (+20%)")

        report_lines.append(s := f"\n👉 **[TQQQ V4.0 가이드 (T={state['TQQQ']['T']:.1f} 회차 / 사이클 #{state['TQQQ']['cycle']})]**")
        report_lines.append(f"  - **별지점 LOC 매수**: `${tqqq_v4['buy_point']:.2f}` (별% {tqqq_v4['star_pct']:+.2f}%) | 수량: `{tqqq_shares}주` (배수: `{tqqq_mult}x`)")
        report_lines.append(f"  - **쿼터매도(25%)**: `{tqqq_q_qty}주` @ 별지점 `${tqqq_v4['star_point']:.2f}` (LOC)")
        report_lines.append(f"  - **최종지정가매도({75 if tqqq_q_qty > 0 else 100}%)**: `{tqqq_m_qty}주` @ `${tqqq_v4['take_profit_price']:.2f}` (+15%)")
        
        report_lines.append(f"\n💡 *V4.0 공식: 일일 매수금 = 잔금 / (40 - T)*")
    else:
        report_lines.append("• **V4.0 모드**: *[하락장 방어 중 - 신규 매수 일시정지]*")
        report_lines.append(f"  - 나스닥이 200일선 아래이므로 매수를 중단하고 **현금(${cash_usd:,.2f})을 보호**합니다.")

    return "\n".join(report_lines)
