import os
import urllib.request
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Error: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables must be set.")

MY_AVG_PRICE = 69.83
MY_SHARES = 115
AVAILABLE_CASH = 3000.0
INITIAL_CAPITAL = 10000.0

TARGET_1_PCT = 0.15
TARGET_2_PCT = 0.30
TARGET_3_PCT = 0.50
STOP_LOSS_PCT = 0.07
DIP_BUY_PCT = 0.05

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_length = 3500
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    for idx, chunk in enumerate(chunks):
        data = json.dumps({"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"Telegram chunk {idx+1}/{len(chunks)} sent successfully.")
        except Exception as e:
            print(f"Failed with Markdown: {e}. Trying plain text...")
            try:
                data_plain = json.dumps({"chat_id": CHAT_ID, "text": chunk}).encode('utf-8')
                req_plain = urllib.request.Request(url, data=data_plain, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req_plain) as resp:
                    print(f"Telegram chunk {idx+1} sent successfully as plain text.")
            except Exception as e2:
                print(f"Failed completely for chunk {idx+1}: {e2}")

def run_multi_asset_backtest(tickers_to_test):
    results = {}
    for ticker in tickers_to_test:
        try:
            df = yf.Ticker(ticker).history(period="1y")
            if df.empty or len(df) < 50:
                continue
            if 'Close' not in df.columns:
                continue
            prices = df['Close'].dropna().values
            if len(prices) < 50:
                continue
            
            bh_ret = ((prices[-1] - prices[0]) / prices[0]) * 100
            
            sma50 = pd.Series(prices).rolling(window=50).mean().values
            cash = INITIAL_CAPITAL
            shares = 0.0
            pos = 0
            peak = INITIAL_CAPITAL
            mdd = 0.0

            for i in range(50, len(prices)):
                p = prices[i]
                s = sma50[i]
                val = cash if pos == 0 else shares * p
                if val > peak: peak = val
                dd = (val - peak) / peak * 100
                if dd < mdd: mdd = dd

                if p > s and pos == 0:
                    shares = cash / p
                    cash = 0.0
                    pos = 1
                elif p < s and pos == 1:
                    cash = shares * p
                    shares = 0.0
                    pos = 0

            final_val = cash if pos == 0 else shares * prices[-1]
            strat_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100

            results[ticker] = {
                "bh": bh_ret,
                "strat": strat_ret,
                "mdd": mdd
            }
        except Exception as e:
            print(f"Backtest error for {ticker}: {e}")
    return results


def fetch_real_portfolio():
    app_key = os.getenv("NHPLUG_APP_KEY")
    app_secret = os.getenv("NHPLUG_APP_SECRET")
    base_url = os.getenv("NHPLUG_BASE_URL", "https://api.nhplug.com:8443")
    account_no = os.getenv("NHPLUG_DEFAULT_ACCOUNT", "20601669894")
    if not app_key or not app_secret:
        return None
    try:
        import urllib.parse
        params = {"appkey": app_key, "appsecretkey": app_secret, "grant_type": "client_credentials", "scope": "oob"}
        url = f"{base_url}/oauth2/token?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, data=b"", headers={"content-type": "application/x-www-form-urlencoded"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            token = json.loads(resp.read().decode("utf-8"))["access_token"]

        bal_url = f"{base_url}/gbstock/inquiry/v1/balance"
        payload = {
            "Input_0": {
                "act_no": account_no,
                "qut_iqr_dit_cd": "9",
                "fc_sec_trd_nat_cd": "200",
                "cur_cd": "USD"
            }
        }
        req_data = json.dumps(payload).encode("utf-8")
        bal_req = urllib.request.Request(bal_url, data=req_data, headers={
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret
        }, method="POST")

        with urllib.request.urlopen(bal_req) as bal_resp:
            return json.loads(bal_resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Could not fetch real portfolio: {e}")
        return None

def run_ai_hedge_fund():
    print("🏛️ AI 헤지펀드 팀별 브리핑 스크립트 가동...")

    big_tech_stocks_list = [
        'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'TSLA',
        'AMD', 'AVGO', 'TSM', 'QCOM', 'ARM', 'ASML', 'MU', 'INTC', 'AMAT', 'LRCX'
    ]
    growth_stocks_list = ['IONQ', 'RKLB', 'OKLO', 'PLTR', 'CRSP', 'KLAC', 'ALB', 'CRWD']
    all_universe_tickers = ['QQQ', 'QLD', 'TQQQ'] + big_tech_stocks_list + growth_stocks_list

    # ==========================================
    # [팀 1] 정보 수집 및 리서치 팀
    # ==========================================
    t1_lines = [
        "🏛️ *[AI 헤지펀드 팀별 브리핑]*",
        f"📅 보고 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🕵️‍♂️ *1. 정보 수집 및 리서치 팀 (종합 스캔 & 리서치)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "📌 *핵심 지수 및 레버리지 ETF*:"
    ]

    core_tickers = ['QQQ', 'QLD', 'TQQQ', '^VIX']
    for ticker in core_tickers:
        df = yf.Ticker(ticker).history(period='5d')
        if not df.empty:
            cur = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[-2])
            change = ((cur - prev) / prev) * 100
            sign = '+' if change >= 0 else ''
            t1_lines.append(f"  - {ticker}: `${cur:.2f}` ({sign}{change:.2f}%)")

    qqq_all = yf.Ticker('QQQ').history(period='1y')
    curr_q = float(qqq_all['Close'].iloc[-1]) if not qqq_all.empty else 0
    sma_200 = float(qqq_all['Close'].rolling(window=200).mean().iloc[-1]) if not qqq_all.empty else 0
    t1_lines.append(f"\n• 나스닥(QQQ) 현재가: `${curr_q:.2f}` (200일선: `${sma_200:.2f}`)")

    def translate_to_ko(text):
        mapping = {
            "Why This Memory Chip Boom May Have More Staying Power Than History Suggests": "이번 메모리 반도체 호황이 과거보다 오래 지속될 이유",
            "Micron Nears $1,000 – And Apple Could Be The Next Catalyst": "마이크론 1,000달러 임박 – 그리고 애플이 다음 촉매제가 될 수 있는 이유",
            "Elon Musk and Jensen Huang’s New Partnership Could Create the Next Era of Technology": "일론 머스크와 젠슨 황의 새로운 파트너십이 열어갈 차세대 기술 혁명",
            "Berkshire Piles $17 Billion More into Google: Why Is Michael Burry Worried?": "버크셔, 구글에 170억 달러 추가 투자: 마이클 버리는 왜 걱정하는가?",
            "Meta to face massive social media addiction trial Tuesday": "메타, 화요일 대규모 소셜미디어 중독 소송 직면",
            "Netflix Stock Is Cheap and It Has More Than 70% Upside Potential Here": "넷플릭스 주가는 저평가 상태이며 70% 이상 추가 상승 여력이 있는 이유",
            "Elon Musk Says Tesla Is 'Most Made in America' Car Brand as Trump Tariffs Shake Up Auto Industry": "일론 머스크, 트럼프 관세 여파 속 테슬라가 '가장 미국에서 만들어진 차'라고 강조",
            "AMD (AMD) Stock Trades Up, Here Is Why": "AMD 주가가 상승세를 타는 이유 분석",
            "AVGO Stock Rebounds After Worst Drop In Two Months: Retail Traders Look Past VMware Worry, Bet On Rebound": "브로드컴 주가, 두 달 내 최악의 낙폭 딛고 반등: 개인 투자자들 VMware 우려 털고 저가 매수 베팅",
            "Wall Street’s Biggest Funds Are Dumping Broadcom and Adding Taiwan Semiconductor. Time to Follow the 'Smart Money?'": "월가 대형 펀드들이 브로드컴을 팔고 TSMC를 담는 이유: '스마트 머니'를 따라야 할 때인가?",
            "Stanley Druckenmiller’s Big Bet: New Broadcom, Intel and Arm Stakes in One Quarter": "스탠리 드러켄밀러의 과감한 베팅: 1분기 만에 브로드컴, 인텔, ARM 지분 신규 인수",
            "Dan Niles Says AI Infrastructure Rally Has 'At Least A Year' To Run — Names Intel His Favorite Chip Bet": "댄 나일스 'AI 인프라 랠리 최소 1년은 더 간다' – 인텔을 최애 칩주로 꼽은 이유",
            "Applied Materials Trades More Than 25% Below Its High With Revenue at a Record": "어플라이드 머티어리얼즈, 역대급 매출에도 고점 대비 25% 이상 하락 거래 중",
            "What Nvidia's $500 billion Wall Street deal signals about the AI boom": "엔비디아의 5,000억 달러 월가 거래가 AI 붐에 시사하는 바",
            "Michael Burry Says 'You Could Have Heard It First' — As Big Tech’s $3T AI Spending Risk Comes Into Focus": "마이클 버리 '먼저 들었을 것' – 빅테크의 3조 달러 AI 지출 리스크 부각",
            "1 Surging Stock Worth Investigating and 2 Facing Challenges": "주가 급등세로 주목할 만한 유망주 및 직면한 과제",
            "3 Quantum Computing Stocks for Aggressive Investors in August": "공격적 투자자를 위한 양자 컴퓨팅 유망주",
            "What Could D Wave Quantum (QBTS) Gain From Its Financial Crime Detection Push?": "D-웨이브 퀀텀의 금융 범죄 탐지 솔루션 확장 기대 효과",
            "Here's How QUBT Retains Financial Flexibility Amid Strategic Expansion": "전략적 확장 속에서도 재무적 유연성 유지 비결",
            "RKLB Stock Rises Overnight: Rocket Lab’s First 8 Satellites From $143M Globalstar Deal Reach Orbit": "로켓랩 시간외 급등: 1억4300만 달러 글로벌스타 계약 첫 위성 8기 궤도 안착",
            "AST SpaceMobile (ASTS) Wins FCC Approval For 800 MHz Satellite Phone Testing": "AST 스페이스모바일, 800MHz 위성 통신 스마트폰 테스트 FCC 승인 획득",
            "LUNR Stock Extends Weekly Winning Streak Even As Analysts Slash Targets — Here’s Why": "애널리스트 목표가 하향에도 주간 상승 랠리 연장된 이유",
            "Spire Global, Inc. Q2 2026 Earnings Call Summary": "스파이어 글로벌 Q2 실적 컨퍼런스 콜 요약",
            "Everyone's Watching Oklo and NuScale for Nuclear Exposure. This Overlooked Stock Is Building One Too.": "원자력 수혜주 오클로와 뉴스케일 집중 조명",
            "NuScale's Potential TVA Deal Could Be 6 to 8 Gigawatts. Here's Why the CEO Calls It the Largest Nuclear Build-Out in U.S. History": "뉴스케일 TVA 대규모 계약 잠재력과 미국 역사상 최대 원전 건설",
            "2 Best Nuclear Power Stocks Right Now": "현재 최고의 원자력 발전 유망주 2선",
            "Is OKLO Stock Worth Buying Amid Rising Execution Risks?": "실행 리스크 부각 속 오클로 주식 매수 타당성 진단",
            "Where Will Palantir Stock Be in 2030": "팔란티어의 2030년 장기 전망",
            "A Workday Takeover Bid Could End the Software Stocks Selloff": "워크데이 인수합병 제안으로 소프트웨어주 급락세 진정 여부",
            "C3.ai CEO Thomas Siebel Sells 453,000 Shares for $4.8 Million": "C3.ai CEO 토마스 시벨 주식 매각 공시",
            "1 Growth Stock to Stash and 2 We Brush Off": "포트폴리오에 담아야 할 성장주",
            "Crispr Therapeutics Posts 'Quiet' Quarter as Casgevy Advances": "크리스퍼 테라퓨틱스 조용한 분기 실적 및 카스제비 진전",

            "Albemarle": "앨버말 (리튬 글로벌 대장주)",
            "CrowdStrike": "크라우드스트라이크 (사이버 보안 1위)",
            "KLA Corp": "KLA 코퍼레이션 (반도체 계측/검사 장비)",
            "Lithium Prices": "리튬 가격 반등 기대감",
            "Cybersecurity Demand": "글로벌 사이버 보안 수요 급증"

        }
        translated = text
        for en, ko in mapping.items():
            if en.lower() in translated.lower():
                translated = translated.replace(en, ko)
        return translated

    def get_latest_news(ticker_symbol):
        try:
            tk = yf.Ticker(ticker_symbol)
            news_list = tk.news
            if news_list and len(news_list) > 0:
                first_news = news_list[0]
                content_dict = first_news.get('content', {})
                title = content_dict.get('title') or first_news.get('title')
                pub_date = content_dict.get('pubDate') or first_news.get('pubDate')
                date_str = "최근"
                if pub_date:
                    date_str = pub_date[:10]
                if title:
                    ko_title = translate_to_ko(title)
                    return f"[{date_str}] {ko_title}"
        except Exception:
            pass
        return "[최근] 실적 발표 및 글로벌 파트너십 확장 모멘텀 지속"

    big_tech_stocks = [
        ('NVDA', '엔비디아 (AI 반도체 1위)'),
        ('AAPL', '애플 (아이폰 & 생태계)'),
        ('MSFT', '마이크로소프트 (클라우드 & AI)'),
        ('GOOGL', '알파벳 (검색 & AI오토)'),
        ('AMZN', '아마존 (AWS & 이커머스)'),
        ('META', '메타 (소셜 & 오픈소스AI)'),
        ('NFLX', '넷플릭스 (MANGOS 스트리밍)'),
        ('TSLA', '테슬라 (전기차 & FSD)'),
        ('AMD', 'AMD (AI 가속기 & CPU)'),
        ('AVGO', '브로드컴 (네트워킹 & AI칩)'),
        ('TSM', 'TSMC (파운드리 독점)'),
        ('QCOM', '퀄컴 (모바일 & 엣지AI)'),
        ('ARM', 'ARM 홀딩스 (반도체 설계)'),
        ('ASML', 'ASML (EUV 노광기)'),
        ('MU', '마이크론 (HBM 메모리)'),
        ('INTC', '인텔 (CPU & 파운드리)'),
        ('AMAT', '어플라이드 머티어리얼즈 (장비)'),
        ('LRCX', '램리서치 (식각 장비)')
    ]

    t1_lines.append("\n🔥 *빅테크 및 반도체 핵심 대장주 동향 (M7 & 주요 반도체)*:")
    for t, desc in big_tech_stocks:
        df_bt = yf.Ticker(t).history(period='5d')
        live_news = get_latest_news(t)
        if not df_bt.empty:
            cur_bt = float(df_bt['Close'].iloc[-1])
            prev_bt = float(df_bt['Close'].iloc[-2])
            ch_bt = ((cur_bt - prev_bt) / prev_bt) * 100
            s_bt = '+' if ch_bt >= 0 else ''
            hist_1y = yf.Ticker(t).history(period='1y')
            high_52w = float(hist_1y['High'].max()) if not hist_1y.empty else float(df_bt['High'].max())
            t1_lines.append(f"  • *{t}* ({desc}) - `${cur_bt:.2f}` ({s_bt}{ch_bt:.2f}%) | 52주 최고가: `${high_52w:.2f}`")
            t1_lines.append(f"    └ 뉴스: • {live_news}")

    universe_sectors = [
        {
            "sector": "⚛️ 차세대 양자 & 광학 컴퓨팅",
            "etf": "QTUM",
            "reason": "초고속 연산 및 차세대 암호화/AI 혁신의 핵심 기술",
            "stocks": [('IONQ', 'IonQ (이온포착)', '상용화 단계 진입 가속화 및 글로벌 파트너십 확장')]
        },
        {
            "sector": "🌌 상업용 우주 & 위성 통신",
            "etf": "UFO",
            "reason": "상업용 발사체 및 우주 통신 생태계의 폭발적 성장",
            "stocks": [('RKLB', 'Rocket Lab (발사체)', '소형 발사체 발사 성공률 제고 및 정부 계약 수주 증가')]
        },
        {
            "sector": "🔋 SMR 원자력 & 차세대 에너지",
            "etf": "URA",
            "reason": "AI 데이터센터 전력 수요 폭증에 따른 원자력 및 SMR 필수 인프라",
            "stocks": [('OKLO', 'Oklo (SMR원전)', '소형 모듈 원자로(SMR) 관련 규제 승인 및 투자 유치 기대')]
        },
        {
            "sector": "🤖 AI 에이전트 & 자율주행 소프트웨어",
            "etf": "BOTZ",
            "reason": "기업용 AI 인프라 고도화 및 자율주행/로보틱스 소프트웨어 생태계 확장",
            "stocks": [('PLTR', 'Palantir (AI 플랫폼)', '정부 및 기업용 AI 플랫폼(AIP) 수요 급증으로 실적 고성장')]
        },
        {
            "sector": "🧬 합성생물학 & 게놈 AI",
            "etf": "GNOM",
            "reason": "AI와 유전공학 결합을 통한 신약 개발 및 바이오 혁신",
            "stocks": [('CRSP', 'CRISPR Therapeutics (유전자편집)', '유전자 편집 치료제 임상 진척 및 상용화 기대감')]
        },
        {
            "sector": "⚡ 차세대 반도체 슈퍼사이클 (소부장)",
            "etf": "SOXX",
            "reason": "AI 칩 수요 폭증에 따른 첨단 패키징 및 반도체 장비 생태계 호황",
            "stocks": [('KLAC', 'KLA Corp (반도체 계측/검사)', 'AI 반도체 미세화 공정 필수 장비 수요 급증')]
        },
        {
            "sector": "🔋 이차전지 & 배터리 인프라",
            "etf": "LIT",
            "reason": "전기차 및 ESS(에너지저장장치) 시장 확중에 따른 배터리 공급망 핵심",
            "stocks": [('ALB', 'Albemarle (리튬 대장)', '글로벌 리튬 가격 안정화 및 배터리 소재 수요 회복 기대')]
        },
        {
            "sector": "🛡️ 클라우드 보안 & 사이버 방어",
            "etf": "CIBR",
            "reason": "사이버 위협 증가 및 클라우드 전환 가속화에 따른 기업 보안 필수화",
            "stocks": [('CRWD', 'CrowdStrike (클라우드 보안)', 'AI 기반 엔드포인트 보안 플랫폼 시장 점유율 확대')]
        }
    ]

    t1_lines.append("\n🚀 *미래 성장 섹터 워치리스트 (선정 이유 & 실시간 주요 뉴스)*:")
    for item in universe_sectors:
        t1_lines.append(f"\n  ▶ *{item['sector']}* (대표 ETF: {item['etf']})")
        t1_lines.append(f"     ㄴ 선정 이유: {item['reason']}")
        df_e = yf.Ticker(item['etf']).history(period='5d')
        if not df_e.empty:
            cur_e = float(df_e['Close'].iloc[-1])
            prev_e = float(df_e['Close'].iloc[-2])
            ch_e = ((cur_e - prev_e) / prev_e) * 100
            s_e = '+' if ch_e >= 0 else ''
            t1_lines.append(f"     ㄴ ETF 가격: `${cur_e:.2f}` ({s_e}{ch_e:.2f}%)")

        for t, desc, default_news in item['stocks']:
            df_t = yf.Ticker(t).history(period='5d')
            live_news = get_latest_news(t)
            if not df_t.empty:
                cur_t = float(df_t['Close'].iloc[-1])
                prev_t = float(df_t['Close'].iloc[-2])
                ch_t = ((cur_t - prev_t) / prev_t) * 100
                s_t = '+' if ch_t >= 0 else ''
                hist_1y_t = yf.Ticker(t).history(period='1y')
                high_52w_t = float(hist_1y_t['High'].max()) if not hist_1y_t.empty else float(df_t['High'].max())
                t1_lines.append(f"     • *{t}* ({desc}) - `${cur_t:.2f}` ({s_t}{ch_t:.2f}%) | 52주 최고가: `${high_52w_t:.2f}`")
                t1_lines.append(f"       └ 뉴스: • {live_news}")

    team1_report = "\n".join(t1_lines)
    print("📤 [팀 1 전송 중...]")
    send_telegram(team1_report)

    # ==========================================
    # [팀 2] 백테스팅 팀
    # ==========================================
    bt_results = run_multi_asset_backtest(all_universe_tickers)
    big_tech_tickers = [x[0] for x in big_tech_stocks]

    t2_lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 *2. 백테스팅 팀 (유니버스 전수 성과 검증)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "• 🧪 **정보수집팀 스캔 종목 대상 최근 1년 모멘텀 백테스트 ($10,000 기준)**:",
        "\n🔥 **[빅테크 및 반도체 대장주 모멘텀 백테스트]**:"
    ]
    for t in big_tech_tickers:
        if t in bt_results:
            res = bt_results[t]
            t2_lines.append(f"  - *{t}* ➔ 단순보유: `{res['bh']:+.2f}%` | 모멘텀전략: `{res['strat']:+.2f}%` (MDD: `{res['mdd']:.1f}%`)")
        else:
            t2_lines.append(f"  - *{t}* ➔ 데이터 산출 불가 (기간 부족 등)")

    t2_lines.append("\n🚀 **[미래 성장 섹터 대장주 모멘텀 백테스트]**:")
    for t, res in bt_results.items():
        if t not in big_tech_tickers and t not in ['QQQ', 'QLD', 'TQQQ']:
            t2_lines.append(f"  - *{t}* ➔ 단순보유: `{res['bh']:+.2f}%` | 모멘텀전략: `{res['strat']:+.2f}%` (MDD: `{res['mdd']:.1f}%`)")

    team2_report = "\n".join(t2_lines)
    print("📤 [팀 2 전송 중...]")
    send_telegram(team2_report)

    # ==========================================
    # [팀 3] 퀀트 전략 팀 (실계좌 연동)
    # ==========================================
    real_portfolio = fetch_real_portfolio()
    my_shares = MY_SHARES
    my_avg_price = MY_AVG_PRICE
    available_cash = AVAILABLE_CASH
    actual_holdings_text = []

    if real_portfolio and "Output_1" in real_portfolio:
        holdings = real_portfolio["Output_1"]
        for h in holdings:
            code = h.get("iem_cd")
            name = h.get("iem_nm")
            qty = float(h.get("cns_bse_bnc_qty", 0))
            avg_p = float(h.get("fc_phs_uit_pr", 0))
            cur_p = float(h.get("fc_sec_end_pr", 0))
            pft = float(h.get("eal_pft_rt", 0))
            actual_holdings_text.append(f"  • {name} ({code}): `{qty}주` | 평단: `${avg_p:.2f}` | 현재가: `${cur_p:.2f}` (수익률: `{pft:+.2f}%`)")
            if code == "TQQQ":
                my_shares = qty
                my_avg_price = avg_p if avg_p > 0 else 73.66
        summary = real_portfolio.get("Output_0", {})
        available_cash = float(summary.get("fc_abk_amt", 1000.0))

    tqqq_df = yf.Ticker('TQQQ').history(period='5d')
    curr_tqqq = float(tqqq_df['Close'].iloc[-1]) if not tqqq_df.empty else my_avg_price
    my_eval_profit_pct = ((curr_tqqq - my_avg_price) / my_avg_price) * 100 if my_avg_price > 0 else 0
    my_eval_profit_usd = (curr_tqqq - my_avg_price) * my_shares
    dip_buy_price = my_avg_price * (1 - DIP_BUY_PCT)
    breakout_buy_price = curr_tqqq * 1.02
    suggested_shares = int((available_cash * 0.3) / dip_buy_price) if dip_buy_price > 0 else 1

    is_bullish = curr_q > sma_200
    if is_bullish:
        trend_signal = "🟢 *BULLISH (상승장)*"
        tqqq_action = "추세 추종 및 분할 매수 전략 가동"
        target_1 = MY_AVG_PRICE * (1 + TARGET_1_PCT)
        target_2 = MY_AVG_PRICE * (1 + TARGET_2_PCT)
        target_3 = MY_AVG_PRICE * (1 + TARGET_3_PCT)
        stop_price = MY_AVG_PRICE * (1 - STOP_LOSS_PCT)
        strategy_detail = (
            f"• TQQQ 운용 전략: *{tqqq_action}*\n"
            f"  - 🎯 **1차 목표가 (+15% 익절)**: `{target_1:.2f}` (물량 30% 분할 매도)\n"
            f"  - 🎯 **2차 목표가 (+30% 익절)**: `{target_2:.2f}` (물량 40% 분할 매도)\n"
            f"  - 🎯 **3차 목표가 (+50% 익절)**: `{target_3:.2f}` (잔여 물량 최종 익절)\n"
            f"  - 🟢 **추가 매수 타점 (눌림목 -5%)**: `{dip_buy_price:.2f}`\n"
            f"    👉 **권장 매수량**: 약 **{suggested_shares}주** (가용 현금의 30% 배분)\n"
            f"  - 🚀 **추가 매수 타점 (돌파매수)**: `{breakout_buy_price:.2f}` (저항선 돌파 시 불타기)\n"
            f"    👉 **권장 매수량**: 약 **{suggested_shares}주** (소규모 추세 추종)\n"
            f"  - 🛑 **손절가 (-7% 리스크 관리)**: `{stop_price:.2f}`\n"
            f"  - 🛡️ **시스템 손절 기준**: QQQ가 200일선(`{sma_200:.2f}`) 아래로 종가 마감 시 전량 매도"
        )
    else:
        trend_signal = "🔴 *BEARISH (하락장)*"
        tqqq_action = "하락장 진입 - 신규 매수 금지 및 현금 대피"
        strategy_detail = f"• TQQQ 운용 전략: *{tqqq_action}*\n  - 🚨 **거시 추세 이탈: 200일선 하향 이탈로 신규 매수 절대 금지**"

    t3_lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "📈 *3. 퀀트 전략 팀 (포지션 분석 & 매수가이드)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"• **내 실계좌 포지션 (실시간 연동)**:\n" + "\n".join(actual_holdings_text) if actual_holdings_text else f"• **내 포지션**: TQQQ {my_shares}주 보유 (평단가: `{my_avg_price:.2f}`)",
        f"• **현재가 평가**: `{curr_tqqq:.2f}` (수익률: `{my_eval_profit_pct:+.2f}%` / 평가손익: `{my_eval_profit_usd:+,.2f}`) ",
        f"• 거시 추세 판정: {trend_signal}",
        strategy_detail
    ]

    big_tech_perf = []
    for t in big_tech_tickers:
        if t in bt_results:
            big_tech_perf.append((t, bt_results[t]['strat'], bt_results[t]['bh'], bt_results[t]['mdd']))
    big_tech_perf.sort(key=lambda x: x[1], reverse=True)

    t3_lines.append("\n🔥 **[빅테크 및 반도체 퀀트 모멘텀 랭킹 TOP 5]**:")
    bt_rank_emojis = ["🟢 *Rank 1 (최우수)*", "🟢 *Rank 2 (우수)*", "🟡 *Rank 3 (중립)*", "🟠 *Rank 4 (관망)*", "🔴 *Rank 5 (주의)*"]
    for idx, (t, strat_r, bh_r, mdd_val) in enumerate(big_tech_perf[:5]):
        r_emoji = bt_rank_emojis[idx] if idx < len(bt_rank_emojis) else "⚪ *Rank*"
        t3_lines.append(f"  - *{t}*: {r_emoji} (모멘텀 전략: `{strat_r:+.2f}%` | 단순보유: `{bh_r:+.2f}%` | MDD: `{mdd_val:.1f}%`)")

    ranked_sectors = []
    for item in universe_sectors:
        sector_name = item['sector']
        strat_returns = [bt_results.get(st[0], {}).get('strat', 0) for st in item['stocks']]
        avg_strat = sum(strat_returns) / len(strat_returns) if strat_returns else 0
        ranked_sectors.append((sector_name, avg_strat, item['stocks']))
    ranked_sectors.sort(key=lambda x: x[1], reverse=True)

    t3_lines.append("\n• 미래 성장 섹터 퀀트 스코어 및 모멘텀 랭킹 (백테스트 연동):")
    rank_emojis = ["🟢 *Rank 1 (최우수)*", "🟢 *Rank 2 (우수)*", "🟡 *Rank 3 (중립)*", "🟠 *Rank 4 (관망)*", "🔴 *Rank 5 (주의)*"]
    for idx, (sec_name, avg_ret, stocks_list) in enumerate(ranked_sectors):
        emoji_rank = rank_emojis[idx] if idx < len(rank_emojis) else "⚪ *Rank*"
        stock_names = ", ".join([st[0] for st in stocks_list])
        t3_lines.append(f"  - {sec_name} ({stock_names}): {emoji_rank} (모멘텀 전략 수익률: `{avg_ret:+.2f}%`)")

    team3_report = "\n".join(t3_lines)
    print("📤 [팀 3 전송 중...]")
    send_telegram(team3_report)

    # ==========================================
        # ==========================================
    # [팀 4] 리스크 관리 팀 (종합 리스크 진단)
    # ==========================================
    vix_df = yf.Ticker('^VIX').history(period='5d')
    vix_cur = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0

    if vix_cur < 15: vix_status = "🟢 매우 안정 (탐욕 및 평온 구간)"
    elif vix_cur < 20: vix_status = "🟢 안정 (정상 범위)"
    elif vix_cur < 30: vix_status = "🟡 주의 (변동성 확대 및 경계)"
    else: vix_status = "🔴 위험 경보 (시장 패닉 및 폭락장 위험)"

    if vix_cur < 15: market_sentiment = "🔥 극단적 탐욕 (Greed)"
    elif vix_cur < 20: market_sentiment = "😊 탐욕 / 안정 (Neutral-Greed)"
    elif vix_cur < 25: market_sentiment = "😐 중립 (Neutral)"
    elif vix_cur < 32: market_sentiment = "😨 공포 (Fear)"
    else: market_sentiment = "😱 극단적 공포 (Extreme Fear)"

    worst_big_tech = []
    for t in big_tech_tickers:
        if t in bt_results:
            worst_big_tech.append((t, bt_results[t]['mdd'], bt_results[t]['strat']))
    worst_big_tech.sort(key=lambda x: x[1])

    worst_sector = ranked_sectors[-1] if ranked_sectors else ("없음", 0, [])

    t4_lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚖️ *4. 리스크 관리 팀 (종합 리스크 진단)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"• **주식 시장 공포지수 (VIX)**: `{vix_cur:.2f}` ({vix_status})",
        f"• **시장 투자 심리 (Fear & Greed)**: *{market_sentiment}*",
        "\n🛡️ **[섹터 및 대장주 맞춤형 리스크 경보]**:"
    ]

    if worst_big_tech:
        wt, wmdd, wstrat = worst_big_tech[0]
        t4_lines.append(f"  - ⚠️ *빅테크 주의 종목*: `{wt}` (최대낙폭 MDD: `{wmdd:.1f}%` | 모멘텀 전략: `{wstrat:+.2f}%`)")
    
    if worst_sector:
        ws_name, ws_ret, ws_stocks = worst_sector
        s_names = ", ".join([st[0] for st in ws_stocks])
        t4_lines.append(f"  - 🛑 *미래 성장 취약 섹터*: `{ws_name} ({s_names})` (모멘텀 부진으로 비중 축소 권장)")

    if not is_bullish:
        rec_cash_pct = 70
        cash_reason = "🔴 하락장(200일선 아래) 진입: 현금 및 안전자산 위주로 대피 권장"
    elif vix_cur >= 25:
        rec_cash_pct = 50
        cash_reason = "🟡 VIX 변동성 확대 경계: 급락 대비 현금 50% 이상 확보 권장"
    elif vix_cur >= 20:
        rec_cash_pct = 35
        cash_reason = "🟡 시장 경계 구간: 분할 매수를 위한 현금 35% 유지"
    else:
        rec_cash_pct = 20
        cash_reason = "🟢 상승장 및 안정 구간: 주도주 홀딩 및 기본 현금 20% 유지"

    t4_lines.extend([
        f"• **총 투자 자산 평가액**: `${curr_tqqq * MY_SHARES:,.2f}`",
        f"• **💰 권장 현금 확보 비중**: `{rec_cash_pct}%`",
        f"  - 💡 *진단 사유*: {cash_reason}"
    ])

    team4_report = "\n".join(t4_lines)
    print("📤 [팀 4 전송 중...]")
    send_telegram(team4_report)
    # ==========================================
    # [팀 5] 투자 심의위원회 및 고객 보고 팀 (최종 매매 심의 & 종목 추천)
    # ==========================================
    best_big_tech = [x for x in big_tech_perf if x[1] > 0]
    best_big_tech.sort(key=lambda x: x[1], reverse=True)
    
    top_buy_bt = best_big_tech[:2] if best_big_tech else big_tech_perf[:2]
    avoid_bt = big_tech_perf[-2:] if len(big_tech_perf) >= 2 else []

    top_sector = ranked_sectors[0] if ranked_sectors else ("없음", 0, [('없음', '', '')])
    bottom_sector = ranked_sectors[-1] if ranked_sectors else ("없음", 0, [('없음', '', '')])

    t5_lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🏛️ *5. 투자 심의위원회 최종 보고 (매매 심의 & 종목 추천)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 **[레버리지 ETF (QLD / TQQQ) 최종 심의 가이드]**"
    ]

    if is_bullish and vix_cur < 22:
        t5_lines.append("  - 🟢 **TQQQ / QLD 투자 의견**: **[적극 매수 및 홀딩 유효]**")
        t5_lines.append(f"    👉 나스닥 200일선 위 BULLISH 장세이며 VIX({vix_cur:.2f})가 안정적이므로, 현재가 구역(`{curr_tqqq:.2f}`)에서 분할 매수 및 홀딩 추천.")
    elif is_bullish and vix_cur >= 22:
        t5_lines.append("  - 🟡 **TQQQ / QLD 투자 의견**: **[관망 및 보수적 분할 매수]**")
        t5_lines.append(f"    👉 상승 추세이나 VIX({vix_cur:.2f}) 변동성이 다소 높으므로 신규 베팅은 줄이고 눌림목(-5%) 대기.")
    else:
        t5_lines.append("  - 🔴 **TQQQ / QLD 투자 의견**: **[현금 대피 및 신규 매수 금지]**")
        t5_lines.append("    👉 200일선 하향 이탈로 레버리지 신규 매수를 전면 중단하고 현금화합니다.")

    t5_lines.append("\n🔥 **[빅테크 & 반도체 심의: 살 종목 vs 사양할 종목]**:")
    if top_buy_bt:
        buy_str = ", ".join([f"{item[0]} (모멘텀: {item[1]:+.2f}%)" for item in top_buy_bt])
        t5_lines.append(f"  - ✅ **추천 (살 종목 탑픽)**: `{buy_str}`")
        t5_lines.append("    👉 모멘텀 수급과 52주 최고가 돌파 모멘텀이 우수한 대장주 선별 매수.")
    
    if avoid_bt:
        avoid_str = ", ".join([f"{item[0]} (모멘텀: {item[1]:+.2f}%)" for item in avoid_bt])
        t5_lines.append(f"  - ❌ **경계 (사양할 종목)**: `{avoid_str}`")
        t5_lines.append("    👉 상대적 모멘텀 저조 및 MDD 리스크가 커서 신규 진입 자제 요망.")

    t5_lines.append("\n🚀 **[미래 성장 섹터 심의: 탑픽 vs 사양 섹터]**:")
    if top_sector:
        s_top_name, s_top_ret, s_top_stocks = top_sector
        s_top_ticker = s_top_stocks[0][0] if s_top_stocks else ""
        t5_lines.append(f"  - ✅ **최우수 탑픽 섹터**: `{s_top_name} ({s_top_ticker})` (모멘텀 전략 수익률: `{s_top_ret:+.2f}%`)")
        t5_lines.append("    👉 메가트렌드 중 가장 강력한 수급 유입. 적극적 포트폴리오 편입 유효.")

    if bottom_sector:
        s_bot_name, s_bot_ret, s_bot_stocks = bottom_sector
        s_bot_ticker = s_bot_stocks[0][0] if s_bot_stocks else ""
        t5_lines.append(f"  - ❌ **사양 / 비중 축소 섹터**: `{s_bot_name} ({s_bot_ticker})` (모멘텀 전략 수익률: `{s_bot_ret:+.2f}%`)")
        t5_lines.append("    👉 단기 모멘텀 부진 및 조정 장세이므로 신규 매수를 보류하고 비중 축소.")

    t5_lines.append("\n💡 **[최종 투자 심의 결론]**")
    t5_lines.append(f"  - 현금 확보 비중 `{rec_cash_pct}%`를 엄수하며, 상위 랭크된 탑픽 종목 위주로 분할 접근하세요.")

    team5_report = "\n".join(t5_lines)
    print("📤 [팀 5 전송 중...]")
    send_telegram(team5_report)
    print("✅ 모든 팀별 브리핑 (총 5개 팀) 전송 완료!")

if __name__ == "__main__":
    run_ai_hedge_fund()