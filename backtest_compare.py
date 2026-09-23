import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def run_comparison_backtest():
    print("🚀 [TQQQ 백테스트 비교: 단순 보유 vs 표준 VR 5.0 vs 동적 현금 VR 5.0]")
    
    ticker = "TQQQ"
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    prices = df["Close"].dropna()
    dates = prices.index
    
    # 200일 이동평균선 계산
    sma_200 = prices.rolling(window=200).mean()
    
    initial_capital = 20000.0
    start_price = float(prices.iloc[0])
    
    # 공통 초기 조건 (주식 50%, 현금 50%)
    init_shares = (initial_capital * 0.5) / start_price
    init_cash = initial_capital * 0.5
    
    # 1. Buy & Hold
    bh_shares = initial_capital / start_price
    bh_values = [bh_shares * p for p in prices]
    
    # 2. 표준 VR 5.0
    vr_shares = init_shares
    vr_cash = init_cash
    vr_V = initial_capital
    vr_values = []
    
    # 3. 동적 현금 VR 5.0 (200일선 필터 적용)
    dyn_shares = init_shares
    dyn_cash = init_cash
    dyn_V = initial_capital
    dyn_values = []
    
    cycle_days = 14
    day_counter = 0
    
    for i in range(len(prices)):
        p = float(prices.iloc[i])
        sma = float(sma_200.iloc[i]) if not pd.isna(sma_200.iloc[i]) else p
        
        # 표준 VR 밸류에이션
        vr_stock_eval = vr_shares * p
        vr_values.append(vr_stock_eval + vr_cash)
        
        # 동적 VR 밸류에이션
        dyn_stock_eval = dyn_shares * p
        dyn_values.append(dyn_stock_eval + dyn_cash)
        
        day_counter += 1
        if day_counter >= cycle_days:
            day_counter = 0
            
            # --- 표준 VR 5.0 리밸런싱 ---
            vr_pool_ratio = (vr_cash / vr_V) if vr_V > 0 else 0.0
            vr_total_rate = (vr_pool_ratio / 10.0) + (0.005 if vr_stock_eval > vr_V else 0.0)
            vr_next_V = vr_V * (1.0 + vr_total_rate)
            vr_v_min = vr_next_V * 0.85
            vr_v_max = vr_next_V * 1.15
            
            if vr_stock_eval < vr_v_min:
                buy_amt = min(vr_next_V - vr_stock_eval, vr_cash * 0.75)
                if buy_amt > 0 and p > 0:
                    bought = buy_amt / p
                    vr_shares += bought
                    vr_cash -= buy_amt
            elif vr_stock_eval > vr_v_max:
                sell_amt = vr_stock_eval - vr_next_V
                if sell_amt > 0 and p > 0:
                    sold = min(sell_amt / p, vr_shares)
                    vr_shares -= sold
                    vr_cash += (sold * p)
            vr_V = vr_next_V
            
            # --- 동적 현금 VR 5.0 리밸런싱 (200일선 추세 필터) ---
            # 가격이 200일선 아래(하락장)면 현금 풀 한도를 100% 개방하여 공격적 매수,
            # 가격이 200일선 위(상승장)면 현금 비중을 조금 더 보수적으로 관리 (G값 가중)
            is_bull = p >= sma
            dyn_pool_limit = 1.0 if not is_bull else 0.70 # 하락장에서는 바닥 쓸어담기 위해 100% 활용
            dyn_G = 8.0 if not is_bull else 12.0 # 하락장에선 G를 낮춰 V 상향 속도 조절, 상승장에선 G를 높여 이익 실현 가속
            
            dyn_pool_ratio = (dyn_cash / dyn_V) if dyn_V > 0 else 0.0
            dyn_total_rate = (dyn_pool_ratio / dyn_G) + (0.005 if dyn_stock_eval > dyn_V else 0.0)
            dyn_next_V = dyn_V * (1.0 + dyn_total_rate)
            dyn_v_min = dyn_next_V * 0.85
            dyn_v_max = dyn_next_V * 1.15
            
            if dyn_stock_eval < dyn_v_min:
                buy_amt = min(dyn_next_V - dyn_stock_eval, dyn_cash * dyn_pool_limit)
                if buy_amt > 0 and p > 0:
                    bought = buy_amt / p
                    dyn_shares += bought
                    dyn_cash -= buy_amt
            elif dyn_stock_eval > dyn_v_max:
                sell_amt = dyn_stock_eval - dyn_next_V
                if sell_amt > 0 and p > 0:
                    sold = min(sell_amt / p, dyn_shares)
                    dyn_shares -= sold
                    dyn_cash += (sold * p)
            dyn_V = dyn_next_V

    # 성과 지표 계산 함수
    def calc_metrics(val_list):
        s = pd.Series(val_list)
        final_val = s.iloc[-1]
        ret = ((final_val - initial_capital) / initial_capital) * 100
        years = (dates[-1] - dates[0]).days / 365.25
        cagr = (((final_val / initial_capital) ** (1 / years)) - 1) * 100
        mdd = ((s / s.cummax()) - 1).min() * 100
        return final_val, ret, cagr, mdd

    bh_final, bh_ret, bh_cagr, bh_mdd = calc_metrics(bh_values)
    vr_final, vr_ret, vr_cagr, vr_mdd = calc_metrics(vr_values)
    dyn_final, dyn_ret, dyn_cagr, dyn_mdd = calc_metrics(dyn_values)

    print("==================================================")
    print("📊 [백테스트 비교 결과 (최근 3년 TQQQ)]")
    print("==================================================")
    print(f"1. 단순 보유 (B&H)")
    print(f"   - 최종 자산: ${bh_final:,.2f} | 수익률: {bh_ret:+.2f}% | CAGR: {bh_cagr:.2f}% | MDD: {bh_mdd:.2f}%")
    print(f"2. 표준 VR 5.0")
    print(f"   - 최종 자산: ${vr_final:,.2f} | 수익률: {vr_ret:+.2f}% | CAGR: {vr_cagr:.2f}% | MDD: {vr_mdd:.2f}%")
    print(f"3. 동적 현금 VR 5.0 (200일선 추세 필터 적용)")
    print(f"   - 최종 자산: ${dyn_final:,.2f} | 수익률: {dyn_ret:+.2f}% | CAGR: {dyn_cagr:.2f}% | MDD: {dyn_mdd:.2f}%")
    print("==================================================")

if __name__ == "__main__":
    run_comparison_backtest()
