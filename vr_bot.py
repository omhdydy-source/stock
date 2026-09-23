import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.plotarea import DataTable
from openpyxl.utils import get_column_letter
from vr_engine import calculate_vr_cycle
from config import TELEGRAM_TOKEN, CHAT_ID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_LOG_PATH = os.path.join(BASE_DIR, "vr_portfolio_log.xlsx")

def update_excel_log(rep):
    target_path = EXCEL_LOG_PATH
    if os.path.exists(target_path):
        try:
            wb = openpyxl.load_workbook(target_path)
        except Exception:
            wb = openpyxl.Workbook()
    else:
        wb = openpyxl.Workbook()

    # 1. Setup Sheet: 루나시트 VR일지 (History Log)
    if "루나시트 VR일지" in wb.sheetnames:
        ws = wb["루나시트 VR일지"]
    else:
        ws = wb.active
        ws.title = "루나시트 VR일지"

    navy_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    light_blue_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    
    font_title = Font(name="맑은 고딕", size=14, bold=True, color="1F4E78")
    font_header = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="맑은 고딕", size=10, bold=True)
    font_normal = Font(name="맑은 고딕", size=10)
    
    thin = Side(border_style="thin", color="D3D3D3")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Title & Summary Cards
    ws.cell(row=1, column=2, value="🚀 라오어식 VR 5.0 오피셜 루나시트 대시보드").font = font_title
    ws.row_dimensions[1].height = 30

    summary_headers = ["총 자산 ($)", "주식 평가금 ($)", "예수금 Pool ($)", "기준 목표선 V ($)", "안전 밴드 하단", "안전 밴드 상단", "진단 액션"]
    summary_vals = [
        rep["total_asset"],
        rep["total_stock_eval"],
        rep["current_Pool"],
        rep["current_V"],
        rep["v_min"],
        rep["v_max"],
        rep["action"]
    ]

    for c_idx, h_text in enumerate(summary_headers, 2):
        c_cell = ws.cell(row=3, column=c_idx, value=h_text)
        c_cell.fill = navy_fill
        c_cell.font = font_header
        c_cell.alignment = Alignment(horizontal="center", vertical="center")
        c_cell.border = border

        v_cell = ws.cell(row=4, column=c_idx, value=summary_vals[c_idx-2])
        v_cell.fill = light_blue_fill
        v_cell.font = font_bold
        v_cell.alignment = Alignment(horizontal="right", vertical="center")
        v_cell.border = border
        if c_idx <= 8:
            v_cell.number_format = "$#,##0.00"
        else:
            v_cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[3].height = 24
    ws.row_dimensions[4].height = 24

    table_headers = [
        "회차", "일자", "TQQQ평단($)", "TQQQ보유수", "주식평가금($)", "Pool현금($)", 
        "총자산($)", "기준목표선V($)", "Pool비중(%)", "G값", "총상승률(%)", 
        "다음목표선(Next V)", "하단선(V min)", "상단선(V max)", "진단결과", "매매필요금액($)"
    ]

    start_row = 7
    # Ensure header is present
    for c_idx, h_text in enumerate(table_headers, 1):
        cell = ws.cell(row=start_row, column=c_idx, value=h_text)
        cell.fill = navy_fill
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[start_row].height = 28

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Find row for today or next empty row
    data_row_idx = start_row + 1
    found_row = None
    while ws.cell(row=data_row_idx, column=1).value is not None and data_row_idx < 1000:
        existing_date = ws.cell(row=data_row_idx, column=2).value
        if existing_date == today_str:
            found_row = data_row_idx
            break
        data_row_idx += 1

    if found_row:
        data_row_idx = found_row
    else:
        # find first empty row after start_row
        data_row_idx = start_row + 1
        while ws.cell(row=data_row_idx, column=1).value is not None and data_row_idx < 1000:
            data_row_idx += 1

    # Calculate sequential index (1, 2, 3, 4, 5...)
    seq_index = 1
    r_chk = start_row + 1
    while r_chk < data_row_idx and ws.cell(row=r_chk, column=1).value is not None:
        seq_index += 1
        r_chk += 1

    row_data = [
        seq_index,
        today_str,
        round(rep["tqqq_avg_p"], 2),
        round(rep["tqqq_qty"], 2),
        round(rep["total_stock_eval"], 2),
        round(rep["current_Pool"], 2),
        round(rep["total_asset"], 2),
        round(rep["current_V"], 2),
        round(rep["pool_ratio"] / 100.0, 4),
        f"/{int(rep['G_value'])}",
        round(rep["total_rate"] / 100.0, 4),
        round(rep["next_V"], 2),
        round(rep["v_min"], 2),
        round(rep["v_max"], 2),
        rep["action"],
        round(rep["trade_amount"], 2)
    ]

    for col_idx, val in enumerate(row_data, 1):
        ws.cell(row=data_row_idx, column=col_idx, value=val)

    # Format all data rows consistently
    curr_r = start_row + 1
    while ws.cell(row=curr_r, column=2).value is not None and curr_r < 1000:
        ws.row_dimensions[curr_r].height = 22
        for c in range(1, 17):
            cell = ws.cell(row=curr_r, column=c)
            val = cell.value
            cell.border = border
            cell.font = font_normal

            if c in [1, 2, 10, 15]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                
            if c in [3, 5, 6, 7, 8, 12, 13, 14, 16]:
                cell.number_format = "$#,##0.00"
            elif c == 4:
                cell.number_format = "#,##0"
            elif c in [9, 11]:
                cell.number_format = "0.00%"
            elif c == 1:
                cell.number_format = "0"
            else:
                cell.number_format = "@"

            if c == 15:
                cell.font = font_bold
                if val == "BUY":
                    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                elif val == "SELL":
                    cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        curr_r += 1

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Charts on history sheet
    ws._charts.clear()

    # Chart 1: 자산 및 평가금 (주식평가금, Pool현금, 총자산)
    chart1 = LineChart()
    chart1.title = "루나시트 VR 5.0 자산 및 평가금 추이"
    chart1.style = 11
    chart1.y_axis.title = "금액 ($)"
    chart1.x_axis.title = "일자"
    chart1.width = 18
    chart1.height = 11
    chart1.legend.position = "r"
    chart1.y_axis.number_format = '$#,##0'
    chart1.plot_area.dTable = DataTable()
    chart1.plot_area.dTable.showHorzBorder = True
    chart1.plot_area.dTable.showVertBorder = True
    chart1.plot_area.dTable.showOutline = True
    chart1.plot_area.dTable.showKeys = True

    # Chart 2: 매수/매도 진단 (주식평가금, 하단선 V min, 기준목표선V, 상단선 V max)
    chart2 = LineChart()
    chart2.title = "루나시트 VR 5.0 매수/매도 진단 차트 (주식평가금 vs V min / V / V max)"
    chart2.style = 11
    chart2.y_axis.title = "금액 ($)"
    chart2.x_axis.title = "일자"
    chart2.width = 18
    chart2.height = 11
    chart2.legend.position = "r"
    chart2.y_axis.number_format = '$#,##0'
    chart2.plot_area.dTable = DataTable()
    chart2.plot_area.dTable.showHorzBorder = True
    chart2.plot_area.dTable.showVertBorder = True
    chart2.plot_area.dTable.showOutline = True
    chart2.plot_area.dTable.showKeys = True

    max_data_row = start_row + 1
    while ws.cell(row=max_data_row, column=1).value is not None and max_data_row < 1000:
        max_data_row += 1
    max_data_row -= 1

    # Populate auxiliary chart columns (Cols 17, 18, 19, 20) for Chart 2 non-destructively
    ws.cell(row=start_row, column=17, value="주식평가금($)").font = font_header
    ws.cell(row=start_row, column=17).fill = navy_fill
    ws.cell(row=start_row, column=18, value="하단선(V min)").font = font_header
    ws.cell(row=start_row, column=18).fill = navy_fill
    ws.cell(row=start_row, column=19, value="기준목표선V").font = font_header
    ws.cell(row=start_row, column=19).fill = navy_fill
    ws.cell(row=start_row, column=20, value="상단선(V max)").font = font_header
    ws.cell(row=start_row, column=20).fill = navy_fill

    curr_r = start_row + 1
    while curr_r <= data_row_idx:
        eval_val = ws.cell(row=curr_r, column=5).value
        v_val = ws.cell(row=curr_r, column=8).value
        vmin_val = ws.cell(row=curr_r, column=13).value
        vmax_val = ws.cell(row=curr_r, column=14).value
        if eval_val is not None:
            ws.cell(row=curr_r, column=17, value=eval_val).number_format = "$#,##0.00"
            ws.cell(row=curr_r, column=18, value=vmin_val).number_format = "$#,##0.00"
            ws.cell(row=curr_r, column=19, value=v_val).number_format = "$#,##0.00"
            ws.cell(row=curr_r, column=20, value=vmax_val).number_format = "$#,##0.00"
        curr_r += 1

    if max_data_row > start_row:
        vals = []
        for r in range(start_row + 1, max_data_row + 1):
            for c in range(5, 11):
                val = ws.cell(row=r, column=c).value
                if isinstance(val, (int, float)):
                    vals.append(val)
        
        calc_max = 25000
        if vals:
            data_max = max(vals)
            calc_max = ((int(data_max) + 4999) // 5000) * 5000

        cats = Reference(ws, min_col=2, min_row=start_row+1, max_row=max_data_row)

        # Add Chart 1 (cols 5 to 7)
        data1 = Reference(ws, min_col=5, min_row=start_row, max_col=7, max_row=max_data_row)
        chart1.add_data(data1, titles_from_data=True)
        chart1.set_categories(cats)
        chart1.y_axis.scaling.min = 0
        chart1.y_axis.scaling.max = calc_max
        chart1.y_axis.crosses = "autoZero"
        chart1.y_axis.tickLblPos = "low"
        chart1.y_axis.majorUnit = 5000
        chart1.y_axis.majorTickMark = "out"
        chart1.y_axis.minorTickMark = "none"
        ws.add_chart(chart1, "R7")

        # Add Chart 2 (cols 17 to 20 for 주식평가금, V min, V, V max)
        data2 = Reference(ws, min_col=17, min_row=start_row, max_col=20, max_row=max_data_row)
        chart2.add_data(data2, titles_from_data=True)
        chart2.set_categories(cats)
        chart2.y_axis.scaling.min = 0
        chart2.y_axis.scaling.max = calc_max
        chart2.y_axis.crosses = "autoZero"
        chart2.y_axis.tickLblPos = "low"
        chart2.y_axis.majorUnit = 5000
        chart2.y_axis.majorTickMark = "out"
        chart2.y_axis.minorTickMark = "none"
        ws.add_chart(chart2, "R27")

    # 2. Setup Separate Sheet: 현재 30단계 가이드 (Current 30-Tier Guide)
    guide_sheet_name = "현재 30단계 가이드"
    if guide_sheet_name in wb.sheetnames:
        ws_g = wb[guide_sheet_name]
        ws_g.cell(row=1, column=1, value="") # clear or reuse
        wb.remove(ws_g)
    ws_g = wb.create_sheet(title=guide_sheet_name)

    today_yy_mm_dd = datetime.now().strftime("%y.%m.%d")
    ws_g.cell(row=1, column=1, value=f"🎯 VR 5.0 현재 30단계 매수/매도 그물망 가이드( {today_yy_mm_dd})").font = font_title
    ws_g.row_dimensions[1].height = 30

    ws_g.cell(row=3, column=1, value="🟢 [매수 30단계 차등가이드]").font = font_bold
    ws_g.cell(row=3, column=6, value="🔴 [매도 30단계 차등가이드]").font = font_bold

    tier_headers = ["회차", "지정가($)", "할당금액($)", "수량(주)"]

    for idx, th in enumerate(tier_headers, 1):
        c = ws_g.cell(row=4, column=idx, value=th)
        c.fill = navy_fill
        c.font = font_header
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border

    for idx, th in enumerate(tier_headers, 6):
        c = ws_g.cell(row=4, column=idx, value=th)
        c.fill = navy_fill
        c.font = font_header
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border

    for i, t in enumerate(rep["buy_tier_orders"]):
        r = 5 + i
        ws_g.cell(row=r, column=1, value=t["tier"]).alignment = Alignment(horizontal="center")
        ws_g.cell(row=r, column=2, value=t["price"]).number_format = "$#,##0.00"
        ws_g.cell(row=r, column=3, value=t["cost"]).number_format = "$#,##0.00"
        ws_g.cell(row=r, column=4, value=t["shares"]).number_format = "#,##0"
        for c in range(1, 5):
            ws_g.cell(row=r, column=c).border = border
            ws_g.cell(row=r, column=c).font = font_normal

    for i, t in enumerate(rep["sell_tier_orders"]):
        r = 5 + i
        ws_g.cell(row=r, column=6, value=t["tier"]).alignment = Alignment(horizontal="center")
        ws_g.cell(row=r, column=7, value=t["price"]).number_format = "$#,##0.00"
        ws_g.cell(row=r, column=8, value=t["revenue"]).number_format = "$#,##0.00"
        ws_g.cell(row=r, column=9, value=t["shares"]).number_format = "#,##0"
        for c in range(6, 10):
            ws_g.cell(row=r, column=c).border = border
            ws_g.cell(row=r, column=c).font = font_normal

    for col in ws_g.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_g.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Ensure all history rows are sequentially numbered (1, 2, 3, ...)
    r_idx_seq = start_row + 1
    seq_val = 1
    while ws.cell(row=r_idx_seq, column=2).value is not None and r_idx_seq < 1000:
        ws.cell(row=r_idx_seq, column=1, value=seq_val)
        ws.cell(row=r_idx_seq, column=1).alignment = Alignment(horizontal="center")
        seq_val += 1
        r_idx_seq += 1

    try:
        wb.save(target_path)
        print(f"📁 구글시트 루나시트 템플릿 양식(깔끔한 시트 분리) 저장 완료: {target_path}")

        # Enforce native Excel rendering of Y-axis ticks/labels via Windows COM automation
        try:
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            wb_com = excel.Workbooks.Open(os.path.abspath(target_path))
            ws_com = wb_com.Sheets("루나시트 VR일지")
            if ws_com.ChartObjects().Count > 0:
                for idx in range(1, ws_com.ChartObjects().Count + 1):
                    chart_com = ws_com.ChartObjects(idx).Chart
                    y_axis_com = chart_com.Axes(2, 1) # xlValue, xlPrimary
                    y_axis_com.MinimumScale = 0
                    y_axis_com.MaximumScale = calc_max
                    y_axis_com.MajorUnit = 5000
            wb_com.Save()
            wb_com.Close()
            excel.Quit()
            print("✨ 엑셀 COM 자동화를 통한 Y축 눈금 및 축 서식 네이티브 렌더링 완료!")
        except Exception as com_err:
            print(f"COM Automation notice: {com_err}")

    except PermissionError:
        alt_path = os.path.join(BASE_DIR, f"vr_portfolio_log_{datetime.now().strftime('%H%M%S')}.xlsx")
        wb.save(alt_path)
        print(f"⚠️ 기존 엑셀 파일이 열려 있어 대체 파일로 저장했습니다: {alt_path}")

def run_vr_bot():
    rep = calculate_vr_cycle()
    update_excel_log(rep)
    print("✅ 루나시트 양식 엑셀 파일 깔끔한 업데이트 완료!")

if __name__ == "__main__":
    run_vr_bot()
