import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def run_monte_carlo_10y():
    print("🔮 [TQQQ VR 5.0 향후 10년 (2,520 거래일) 몬테카를로 미래 시뮬레이션 시작]")
    
    ticker = "TQQQ"
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    prices = df["Close"].dropna()
    log_returns = np.log(prices / prices.shift(1)).dropna()
    
    mu = log_returns.mean()
    sigma = log_returns.std()
    last_price = float(prices.iloc[-1])
    
    print(f"• 기준 현재가 ($): {last_price:.2f}")
    print(f"• 일일 수익률 평균 (Drift): {mu:.5f}, 변동성 (Vol): {sigma:.5f}")
    
    # 향후 10년 (약 2,520 거래일) 1,000개 시나리오 생성
    num_simulations = 1000
    num_days = 2520
    initial_capital = 20000.0
    
    vr_final_assets = []
    bh_final_assets = []
    vr_mdds = []
    bh_mdds = []
    
    np.random.seed(42)
    
    for _ in range(num_simulations):
        sim_returns = np.random.normal(mu, sigma, num_days)
        sim_prices = last_price * np.exp(np.cumsum(sim_returns))
        
        shares = (initial_capital * 0.5) / last_price
        cash = initial_capital * 0.5
        V = initial_capital
        G = 10.0
        band_width = 0.15
        pool_usage_limit = 0.75
        
        bh_shares = initial_capital / last_price
        
        vr_vals = []
        bh_vals = []
        
        day_counter = 0
        for p in sim_prices:
            stock_eval = shares * p
            total_asset = stock_eval + cash
            vr_vals.append(total_asset)
            bh_vals.append(bh_shares * p)
            
            day_counter += 1
            if day_counter >= 14:
                day_counter = 0
                pool_ratio = (cash / V) if V > 0 else 0.0
                basic_rate = pool_ratio / G
                add_rate = 0.005 if stock_eval > V else 0.0
                total_rate = basic_rate + add_rate
                
                next_V = V * (1.0 + total_rate)
                v_min = next_V * (1.0 - band_width)
                v_max = next_V * (1.0 + band_width)
                
                if stock_eval < v_min:
                    buy_amt = min(next_V - stock_eval, cash * pool_usage_limit)
                    if buy_amt > 0 and p > 0:
                        bought = buy_amt / p
                        shares += bought
                        cash -= buy_amt
                elif stock_eval > v_max:
                    sell_amt = stock_eval - next_V
                    if sell_amt > 0 and p > 0:
                        sold = min(sell_amt / p, shares)
                        shares -= sold
                        cash += (sold * p)
                V = next_V
                
        vr_final_assets.append(vr_vals[-1])
        bh_final_assets.append(bh_vals[-1])
        
        vr_ser = pd.Series(vr_vals)
        vr_mdds.append(((vr_ser / vr_ser.cummax()) - 1).min() * 100)
        
        bh_ser = pd.Series(bh_vals)
        bh_mdds.append(((bh_ser / bh_ser.cummax()) - 1).min() * 100)

    vr_final_arr = np.array(vr_final_assets)
    bh_final_arr = np.array(bh_final_assets)
    
    print("\n==================================================")
    print("🎲 [향후 10년 몬테카를로 시뮬레이션 결과 (1,000개 경로, 2,520 거래일)]")
    print("==================================================")
    print(f"• [VR 5.0 전략]")
    print(f"  - 평균 최종 자산: ${np.mean(vr_final_arr):,.2f} (평균 수익률: {((np.mean(vr_final_arr)-initial_capital)/initial_capital)*100:+.2f}%)")
    print(f"  - 상위 10% 대박 시나리오: ${np.percentile(vr_final_arr, 90):,.2f}")
    print(f"  - 하위 10% 최악 시나리오: ${np.percentile(vr_final_arr, 10):,.2f}")
    print(f"  - 평균 최대 낙폭 (MDD): {np.mean(vr_mdds):.2f}%")
    print(f"• [단순 보유 (Buy & Hold)]")
    print(f"  - 평균 최종 자산: ${np.mean(bh_final_arr):,.2f} (평균 수익률: {((np.mean(bh_final_arr)-initial_capital)/initial_capital)*100:+.2f}%)")
    print(f"  - 상위 10% 대박 시나리오: ${np.percentile(bh_final_arr, 90):,.2f}")
    print(f"  - 하위 10% 최악 시나리오: ${np.percentile(bh_final_arr, 10):,.2f}")
    print(f"  - 평균 최대 낙폭 (MDD): {np.mean(bh_mdds):.2f}%")
    print("==================================================")

if __name__ == "__main__":
    run_monte_carlo_10y()
