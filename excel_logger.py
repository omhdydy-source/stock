import os
import pandas as pd
from datetime import datetime
from data_collector import fetch_live_account, fetch_market_data
from quant_engine import load_state
import openpyxl
from openpyxl.chart import LineChart, Reference

EXCEL_FILE = "C:/Users/omh/Desktop/stock/stock_portfolio_log.xlsx"

def log_portfolio_to_excel():
    print("📊 [엑셀 로깅 및 시각화 시스템] 한글화 및 날짜 포맷 적용 중...")
    
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

    # 날짜만 표시 (YYYY-MM-DD)
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    summary_data = [{
        "날짜": today_date,
        "총평가자산(원)": total_asset_krw,
        "예수금($)": cash_usd,
        "주식평가금액($)": tot_eval_usd,
        "평가손익($)": tot_profit_usd,
        "수익률(%)": tot_pft_rt,
        "사이클": state["cycle"],
        "회차": state["tranche"]
    }]
    
    df_summary = pd.DataFrame(summary_data)
    
    holdings_list = []
    if account_data and "Output_1" in account_data:
        for h in account_data["Output_1"]:
            holdings_list.append({
                "날짜": today_date,
                "티커": h.get("iem_cd"),
                "종목명": h.get("iem_nm"),
                "보유수량": float(h.get("cns_bse_bnc_qty", 0)),
                "평균단가($)": float(h.get("fc_phs_uit_pr", 0)),
                "현재가($)": float(h.get("fc_sec_end_pr", 0)),
                "수익률(%)": float(h.get("eal_pft_rt", 0))
            })
            
    df_holdings = pd.DataFrame(holdings_list)
    
    # Read existing or create new with Korean sheet names
    sheet_summary = "자산요약"
    sheet_holdings = "보유종목"
    
    if os.path.exists(EXCEL_FILE):
        try:
            existing_summary = pd.read_excel(EXCEL_FILE, sheet_name=sheet_summary)
            # 중복 날짜 업데이트 또는 누적
            updated_summary = pd.concat([existing_summary, df_summary], ignore_index=True)
        except Exception:
            updated_summary = df_summary
            
        try:
            existing_holdings = pd.read_excel(EXCEL_FILE, sheet_name=sheet_holdings)
            updated_holdings = pd.concat([existing_holdings, df_holdings], ignore_index=True)
        except Exception:
            updated_holdings = df_holdings
    else:
        updated_summary = df_summary
        updated_holdings = df_holdings
        
    # Write back to Excel
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        updated_summary.to_excel(writer, sheet_name=sheet_summary, index=False)
        if not updated_holdings.empty:
            updated_holdings.to_excel(writer, sheet_name=sheet_holdings, index=False)
            
    # Add Visual Charts using openpyxl
    wb = openpyxl.load_workbook(EXCEL_FILE)
    if sheet_summary in wb.sheetnames:
        ws = wb[sheet_summary]
        ws._charts.clear()
        
        max_row = ws.max_row
        if max_row > 1:
            # 1. 총평가자산 차트
            chart = LineChart()
            chart.title = "포트폴리오 총평가자산(원) 추이"
            chart.style = 13
            chart.y_axis.title = "총평가자산 (KRW)"
            chart.x_axis.title = "날짜"
            chart.width = 18
            chart.height = 10
            
            data = Reference(ws, min_col=2, min_row=1, max_row=max_row) # 총평가자산(원)
            cats = Reference(ws, min_col=1, min_row=2, max_row=max_row) # 날짜
            
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            ws.add_chart(chart, "J2")
            
            # 2. 수익률 차트
            chart2 = LineChart()
            chart2.title = "포트폴리오 수익률(%) 추이"
            chart2.style = 2
            chart2.y_axis.title = "수익률 (%)"
            chart2.x_axis.title = "날짜"
            chart2.width = 18
            chart2.height = 10
            
            data2 = Reference(ws, min_col=6, min_row=1, max_row=max_row) # 수익률(%)
            chart2.add_data(data2, titles_from_data=True)
            chart2.set_categories(cats)
            ws.add_chart(chart2, "J18")
            
        wb.save(EXCEL_FILE)
        
    print(f"✅ 엑셀 한글화 및 날짜 포맷 적용 완료: {EXCEL_FILE}")
    return EXCEL_FILE

if __name__ == "__main__":
    log_portfolio_to_excel()
