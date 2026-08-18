import os
import pandas as pd
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data
from quant_engine import load_state
import openpyxl
from openpyxl.chart import LineChart, Reference

EXCEL_FILE = "C:/Users/omh/Desktop/stock/stock_portfolio_log.xlsx"

def log_portfolio_to_excel():
    print("📊 [엑셀 로깅 및 시각화 시스템] 계좌 자산 및 차트 생성 중...")
    
    account_data = fetch_live_account()
    state = load_state()
    
    total_asset_krw = 0
    cash_usd = 0
    tot_eval_usd = 0
    tot_profit_usd = 0
    tot_pft_rt = 0

    if account_data and "Output_0" in account_data:
        summary = account_data["Output_0"]
        total_asset_krw = float(summary.get("tot_aet_amt", 0))
        cash_usd = float(summary.get("fc_aet_amt", 0))
        tot_eval_usd = float(summary.get("fc_eal_amt", 0))
        tot_profit_usd = float(summary.get("fc_eal_pls_amt", 0))
        tot_pft_rt = float(summary.get("pft_rt", 0))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_data = [{
        "Timestamp": timestamp,
        "Total_Asset_KRW": total_asset_krw,
        "Cash_USD": cash_usd,
        "Eval_USD": tot_eval_usd,
        "Profit_USD": tot_profit_usd,
        "Profit_Pct": tot_pft_rt,
        "Cycle": state["cycle"],
        "Tranche": state["tranche"]
    }]
    
    df_summary = pd.DataFrame(summary_data)
    
    holdings_list = []
    if account_data and "Output_1" in account_data:
        for h in account_data["Output_1"]:
            holdings_list.append({
                "Timestamp": timestamp,
                "Ticker": h.get("iem_cd"),
                "Name": h.get("iem_nm"),
                "Qty": float(h.get("cns_bse_bnc_qty", 0)),
                "AvgPrice": float(h.get("fc_phs_uit_pr", 0)),
                "CurPrice": float(h.get("fc_sec_end_pr", 0)),
                "ProfitPct": float(h.get("eal_pft_rt", 0))
            })
            
    df_holdings = pd.DataFrame(holdings_list)
    
    # Read existing or create new
    if os.path.exists(EXCEL_FILE):
        try:
            existing_summary = pd.read_excel(EXCEL_FILE, sheet_name='Summary')
            updated_summary = pd.concat([existing_summary, df_summary], ignore_index=True)
        except Exception:
            updated_summary = df_summary
            
        try:
            existing_holdings = pd.read_excel(EXCEL_FILE, sheet_name='Holdings')
            updated_holdings = pd.concat([existing_holdings, df_holdings], ignore_index=True)
        except Exception:
            updated_holdings = df_holdings
    else:
        updated_summary = df_summary
        updated_holdings = df_holdings
        
    # Write back to Excel using openpyxl for chart addition
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        updated_summary.to_excel(writer, sheet_name='Summary', index=False)
        if not updated_holdings.empty:
            updated_holdings.to_excel(writer, sheet_name='Holdings', index=False)
            
    # Add Visual Chart using openpyxl
    wb = openpyxl.load_workbook(EXCEL_FILE)
    if 'Summary' in wb.sheetnames:
        ws = wb['Summary']
        
        # Remove existing charts if any to avoid duplication
        ws._charts.clear()
        
        max_row = ws.max_row
        if max_row > 1:
            chart = LineChart()
            chart.title = "Portfolio Total Asset (KRW) Trend"
            chart.style = 13
            chart.y_axis.title = "Total Asset (KRW)"
            chart.x_axis.title = "Timestamp"
            chart.width = 18
            chart.height = 10
            
            # Data is in Column B (Total_Asset_KRW), starting from row 1 to max_row
            data = Reference(ws, min_col=2, min_row=1, max_row=max_row)
            # Categories (X-axis) in Column A (Timestamp)
            cats = Reference(ws, min_col=1, min_row=2, max_row=max_row)
            
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            
            ws.add_chart(chart, "J2")
            
            # Profit % Chart
            chart2 = LineChart()
            chart2.title = "Portfolio Profit Percentage (%) Trend"
            chart2.style = 2
            chart2.y_axis.title = "Profit Pct (%)"
            chart2.x_axis.title = "Timestamp"
            chart2.width = 18
            chart2.height = 10
            
            data2 = Reference(ws, min_col=6, min_row=1, max_row=max_row) # Profit_Pct column (Col F)
            chart2.add_data(data2, titles_from_data=True)
            chart2.set_categories(cats)
            
            ws.add_chart(chart2, "J18")
            
        wb.save(EXCEL_FILE)
        
    print(f"✅ 엑셀 로깅 및 시각화(라인 차트 2개 생성) 완료: {EXCEL_FILE}")
    return EXCEL_FILE

if __name__ == "__main__":
    log_portfolio_to_excel()
