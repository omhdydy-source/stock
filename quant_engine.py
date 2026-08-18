import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime

STATE_FILE = "C:/Users/omh/Desktop/stock/infinite_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "SOXL" not in data or "TQQQ" not in data:
                    return {
                        "SOXL": {"cycle": 1, "tranche": 1, "total_tranches": 40},
                        "TQQQ": {"cycle": 1, "tranche": 1, "total_tranches": 40}
                    }
                return data
        except Exception:
            pass
    return {
        "SOXL": {"cycle": 1, "tranche": 1, "total_tranches": 40},
        "TQQQ": {"cycle": 1, "tranche": 1, "total_tranches": 40}
    }

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

    # 보유 종목 수량 파악을 위한 딕셔너리 생성
    holdings_dict = {}
    if account_data and "Output_1" in account_data:
        for h in account_data["Output_1"]:
            code = h.get("iem_cd")
            qty = float(h.get("cns_bse_bnc_qty", 0))
            avg_p = float(h.get("fc_phs_uit_pr", 0))
            cur_p = float(h.get("fc_sec_end_pr", 0))
            pft = float(h.get("eal_pft_rt", 0))
            
            target_pct = 20.0 if code == "SOXL" else 10.0
            target_price = avg_p * (1.0 + target_pct / 100.0) if avg_p > 0 else 0.0
            
            holdings_dict[code] = {
                "qty": qty,
                "avg_p": avg_p,
                "cur_p": cur_p,
                "pft": pft,
                "target_pct": target_pct,
                "target_price": target_price
            }

    # 🔄 스마트 오토 리셋 감지 (보유 수량이 0주이거나 전량 매도된 경우 자동 사이클 리셋)
    state_updated = False
    for ticker in ["SOXL", "TQQQ"]:
        holding_qty = holdings_dict.get(ticker, {}).get("qty", 0.0)
        # 만약 계좌 내 해당 종목 수량이 0이고, 회차가 1회차를 초과했거나 직전 익절 달성 상태였다면 새 사이클로 자동 전환
        if holding_qty == 0 and state[ticker]["tranche"] > 1:
            print(f"🔄 [{ticker}] 보유 수량이 0주입니다. 이전 사이클 익절 완료로 감지하여 사이클 #{state[ticker]['cycle'] + 1}, 1회차로 자동 리셋합니다!")
            state[ticker]["cycle"] += 1
            state[ticker]["tranche"] = 1
            state_updated = True

    if state_updated:
        save_state(state)

    report_lines = [
        "🎯 *[월 10% 목표 라오어 무한매수 + 종목별 독립 퀀트 시스템]*",
        f"📅 보고 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "💼 *1. 실계좌 보유 포지션 및 종목별 무한매수 현황*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"• **총 평가 자산**: `₩{total_asset_krw:,.0f}` (`${total_asset_usd:,.2f}`)",
        f"• **가용 현금 (예수금)**: `${cash_usd:,.2f}`",
        f"• **보유주식 평가금액**: `${tot_eval_usd:,.2f}`",
        f"• **전체 평가 손익**: `${tot_profit_usd:+,.2f}` (`{tot_pft_rt:+.2f}%`)",
        f"• **종목별 진행 회차**:",
        f"  - SOXL: `[ {state['SOXL']['tranche']}회차 / 40회차 ]` (사이클 #{state['SOXL']['cycle']})",
        f"  - TQQQ: `[ {state['TQQQ']['tranche']}회차 / 40회차 ]` (사이클 #{state['TQQQ']['cycle']})\n"
    ]

    if holdings_dict:
        report_lines.append("📌 *보유 종목별 트레이딩 현황 및 독립 익절 목표*:")
        for code, info in holdings_dict.items():
            status_note = f"🎯 익절목표 +{info['target_pct']}% 달성 임박!" if info['pft'] >= (info['target_pct'] - 2.0) else f"진행중 (목표: +{info['target_pct']}%, 목표가: ${info['target_price']:.2f})"
            report_lines.append(f"  • *{code}*: `{info['qty']}주` | 평단: `${info['avg_p']:.2f}` | 현재가: `${info['cur_p']:.2f}`")
            report_lines.append(f"    - 수익률: `{info['pft']:+.2f}%` | 익절목표가: `${info['target_price']:.2f}` (+{info['target_pct']}%) [{status_note}]")

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
            report_lines.append(f"• **공포지수 (VIX)**: `{curr_vix:.2f}` ({vix_status})")

    if fear_greed:
        score = fear_greed["score"]
        rating = fear_greed["rating"].upper()
        report_lines.append(f"• **공포·탐욕 지수 (Fear & Greed)**: `{score:.1f}` ({rating})")

    # Execution Guide
    report_lines.extend([
        "\n━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 *3. 종목별 독립 라오어 무한매수법 실행 가이드*",
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    ])

    if is_bullish:
        soxl_rem = max(1, 40 - state["SOXL"]["tranche"] + 1)
        tqqq_rem = max(1, 40 - state["TQQQ"]["tranche"] + 1)
        
        soxl_budget = min((cash_usd / 2) / soxl_rem, 500.0)
        tqqq_budget = min((cash_usd / 2) / tqqq_rem, 500.0)

        soxl_shares = int(soxl_budget / curr_soxl) if curr_soxl > 0 else 0
        if soxl_shares < 1 and cash_usd >= curr_soxl: soxl_shares = 1
        soxl_cost = soxl_shares * curr_soxl

        tqqq_shares = int(tqqq_budget / curr_tqqq) if curr_tqqq > 0 else 0
        if tqqq_shares < 1 and cash_usd >= curr_tqqq: tqqq_shares = 1
        tqqq_cost = tqqq_shares * curr_tqqq

        report_lines.append("• **무한매수 모드**: *[종목별 독립 정상 진행 중]*")
        
        report_lines.append(f"\n👉 **[SOXL LOC 매수 가이드 ({state['SOXL']['tranche']}회차 / 사이클 #{state['SOXL']['cycle']}) - 익절목표 +20%]**")
        report_lines.append(f"  - **지정가 (이하)**: `${curr_soxl:.2f}` | **수량: `{soxl_shares}주`** (금액: `${soxl_cost:,.2f}`) [익절목표가: `${curr_soxl * 1.2:.2f}`]")

        report_lines.append(f"\n👉 **[TQQQ LOC 매수 가이드 ({state['TQQQ']['tranche']}회차 / 사이클 #{state['TQQQ']['cycle']}) - 익절목표 +10%]**")
        report_lines.append(f"  - **지정가 (이하)**: `${curr_tqqq:.2f}` | **수량: `{tqqq_shares}주`** (금액: `${tqqq_cost:,.2f}`) [익절목표가: `${curr_tqqq * 1.1:.2f}`]")
        
        report_lines.append(f"\n💡 *오늘 밤 정규장 마감 동시호가에 각각 독립된 회차와 가격으로 LOC 주문을 접수하세요.*")
    else:
        report_lines.append("• **무한매수 모드**: *[하락장 방어 중 - 종목별 신규 매수 일시정지]*")
        report_lines.append(f"  - 나스닥이 200일선 아래이므로 신규 매수를 중단하고 **가용 현금(${cash_usd:,.2f})을 보호**합니다.")

    return "\n".join(report_lines)
