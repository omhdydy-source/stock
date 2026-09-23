import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def run_backtest():
    print("🚀 [TQQQ VR 5.0 전략 백테스팅 시작 (최근 3년)]")
    
    # 1. 데이터 다운로드 (최근 3년)
    ticker = "TQQQ"
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    if df.empty:
        print("데이터를 가져오지 못했습니다.")
        return

    prices = df["Close"].dropna()
    dates = prices.index

    # 2. 초기 자본금 설정 ($20,000 기준: 주식 50%, 현금 50%)
    initial_capital = 20000.0
    start_price = float(prices.iloc[0])
    
    initial_shares = (initial_capital * 0.5) / start_price
    initial_cash = initial_capital * 0.5
    
    # Buy & Hold 기준 (처음부터 전액 매수)
    bh_shares = initial_capital / start_price

    # VR 5.0 상태 변수
    V = initial_capital * 0.5 + (initial_shares * start_price) # 초기 목표가치 V
    pool = initial_cash
    G = 10.0 # 기본 G
    band_width = 0.15
    pool_usage_limit = 0.75
    
    shares = initial_shares
    cash = pool
    
    portfolio_values = []
    bh_values = []
    
    cycle_days = 14
    day_counter = 0

    print(f"기간: {dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')}")
    print(f"시작 주가 ($): {start_price:.2f}, 초기 주식수: {shares:.2f}, 초기 현금: ${cash:,.2f}\n")

    for i in range(len(prices)):
        p = float(prices.iloc[i])
        stock_eval = shares * p
        total_asset = stock_eval + cash
        portfolio_values.append(total_asset)
        
        bh_val = bh_shares * p
        bh_values.append(bh_val)
        
        day_counter += 1
        # 14거래일마다 주기 갱신 및 리밸런싱 실행
        if day_counter >= cycle_days:
            day_counter = 0
            
            # VR 공식 적용
            pool_ratio = (cash / V) if V > 0 else 0.0
            basic_rate = pool_ratio / (G / 1.0) # 연간 G 적용 단순화
            add_rate = 0.005 if stock_eval > V else 0.0
            total_rate = basic_rate + add_rate
            
            next_V = V * (1.0 + total_rate)
            v_min = next_V * (1.0 - band_width)
            v_max = next_V * (1.0 + band_width)
            
            if stock_eval < v_min:
                # 매수 필요
                target_stock_val = next_V
                buy_amt = target_stock_val - stock_eval
                max_buy = cash * pool_usage_limit
                actual_buy = min(buy_amt, max_buy)
                if actual_buy > 0 and p > 0:
                    bought_shares = actual_buy / p
                    shares += bought_shares
                    cash -= actual_buy
            elif stock_eval > v_max:
                # 매도 필요
                target_stock_val = next_V
                sell_amt = stock_eval - target_stock_val
                if sell_amt > 0 and p > 0:
                    sold_shares = sell_amt / p
                    if sold_shares > shares:
                        sold_shares = shares
                    shares -= sold_shares
                    cash += (sold_shares * p)
            
            V = next_V

    # 최종 결과 계산
    final_vr_val = portfolio_values[-1]
    final_bh_val = bh_values[-1]
    
    vr_return = ((final_vr_val - initial_capital) / initial_capital) * 100
    bh_return = ((final_bh_val - initial_capital) / initial_capital) * 100
    
    years = (dates[-1] - dates[0]).days / 365.25
    vr_cagr = (((final_vr_val / initial_capital) ** (1 / years)) - 1) * 100
    bh_cagr = (((final_bh_val / initial_capital) ** (1 / years)) - 1) * 100

    # MDD 계산
    pf_series = pd.Series(portfolio_values)
    vr_mdd = ((pf_series / pf_series.cummax()) - 1).min() * 100
    
    bh_series = pd.Series(bh_values)
    bh_mdd = ((bh_series / bh_series.cummax()) - 1).min() * 100

    print("==================================================")
    print("📊 [백테스팅 결과 요약 (최근 3년 TQQQ VR 5.0 vs Buy & Hold)]")
    print("==================================================")
    print(f"• 초기 자본금: ${initial_capital:,.2f}")
    print(f"• VR 5.0 최종 자산: ${final_vr_val:,.2f} (수익률: {vr_return:+.2f}%, CAGR: {vr_cagr:.2f}%, MDD: {vr_mdd:.2f}%)")
    print(f"• 단순 보유 (B&H) 최종 자산: ${final_bh_val:,.2f} (수익률: {bh_return:+.2f}%, CAGR: {bh_cagr:.2f}%, MDD: {bh_mdd:.2f}%)")
    print("==================================================")

if __name__ == "__main__":
    run_backtest()
