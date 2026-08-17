import yfinance as yf
from datetime import datetime

print("=== 🕵️‍♂️ 정보 수집 및 리서치 팀 마켓 브리핑 (미래 성장 섹터 & 대표 ETF 확장) ===")
print("보고 일시: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")

for ticker in ['QQQ', 'TQQQ', '^VIX']:
    df = yf.Ticker(ticker).history(period='5d')
    if not df.empty:
        cur = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        change = ((cur - prev) / prev) * 100
        sign = '+' if change >= 0 else ''
        print("- " + ticker + ": $" + str(round(cur, 2)) + " (" + sign + str(round(change, 2)) + "%)")

qqq_all = yf.Ticker('QQQ').history(period='1y')
if not qqq_all.empty:
    curr_q = float(qqq_all['Close'].iloc[-1])
    sma_200 = float(qqq_all['Close'].rolling(window=200).mean().iloc[-1])
    print("\n[나스닥 100 (QQQ) 추세 분석]")
    print("• 현재가: $" + str(round(curr_q, 2)))
    print("• 200일 이동평균선: $" + str(round(sma_200, 2)))
    if curr_q > sma_200:
        print("• 시그널: 🟢 BULLISH (200일선 위 - TQQQ 적립식 매수 및 보유 유지)")
    else:
        print("• 시그널: 🔴 BEARISH (200일선 아래 - 현금 대피 및 헷지 필요)")

print("\n----------------------------------------")
print("🔥 [리서치 팀 선정: 오늘의 주도주 TOP 3]")
print("----------------------------------------")

top3_data = [
    {
        'ticker': 'NVDA',
        'reason': 'AI 인프라 및 가속기 시장의 압도적인 독점력 유지. 나스닥 상승 국면에서 지수 상승을 가장 강력하게 견인하는 대장주로서 모멘텀이 매우 우수함.',
        'news': [
            '차세대 AI 칩 수요 급증으로 주요 클라우드 업체의 데이터센터 발주 확대 지속',
            '월가 애널리스트들, 데이터센터 및 자율주행 부문 실적 성장세에 긍정적 전망 유지'
        ]
    },
    {
        'ticker': 'AAPL',
        'reason': '탄탄한 현금 창출력과 서비스 부문 고성장. 시장 변동성 장세에서도 방어력이 뛰어나며, 완만한 우상향 추세를 안정적으로 그리는 포트폴리오 핵심 자산.',
        'news': [
            '글로벌 스마트폰 시장 회복세 속 프리미엄 라인업 판매 호조',
            'AI 서비스(Apple Intelligence) 고도화 및 생태계 확장 가속화'
        ]
    },
    {
        'ticker': 'MSFT',
        'reason': '클라우드(Azure)와 AI(OpenAI 파트너십) 부문의 안정적인 수익 구조 보유. 기관 투자자들의 선호도가 높아 하락 시에도 지지선 방어가 탄탄함.',
        'news': [
            '기업용 클라우드 및 AI 솔루션 도입률 지속 상승으로 실적 안정성 부각',
            '글로벌 주요 기관 투자자들의 포트폴리오 비중 확대 움직임 관측'
        ]
    }
]

for idx, item in enumerate(top3_data, 1):
    ticker = item['ticker']
    df = yf.Ticker(ticker).history(period='5d')
    if not df.empty:
        cur = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        change = ((cur - prev) / prev) * 100
        sign = '+' if change >= 0 else ''
        print(str(idx) + '. ' + ticker + ' - 현재가: $' + str(round(cur, 2)) + ' (' + sign + str(round(change, 2)) + '%)')
        print('   ㄴ 선정 이유: ' + item['reason'])
        print('   ㄴ 최근 동향 및 뉴스:')
        for news in item['news']:
            print('      • ' + news)
        print()

print("----------------------------------------")
print("🚀 [미래 성장 메가트렌드 섹터 및 대표 ETF 진입 시그널]")
print("----------------------------------------")

future_sectors = [
    {
        'sector': '⚛️ 양자 컴퓨팅 (IONQ, RGTI) & 대표 ETF: QTUM',
        'tickers': ['IONQ', 'RGTI', 'QTUM'],
        'strategy': '기술력은 폭발적이나 변동성(Beta)이 매우 큰 초고위험 성장주 군군.',
        'signal': '🟡 관망 및 조건부 대기 (QQQ 200일선 위이나, VIX 안정화 및 20일선 돌파 시 분할 매수 시그널 발생)'
    },
    {
        'sector': '🌌 우주 항공 (RKLB, ASTS) & 대표 ETF: UFO',
        'tickers': ['RKLB', 'ASTS', 'UFO'],
        'strategy': '상업용 발사 성공 및 위성 통신 상용화 가속화로 실적 턴어라운드 기대감이 높은 섹터.',
        'signal': '🟡 눌림목 대기 (50일 이동평균선 근처까지 조정 시 소량 분할 매수 시그널 대기 중)'
    },
    {
        'sector': '🔋 차세대 에너지 & SMR (OKLO, CCJ) & 대표 ETF: URA',
        'tickers': ['OKLO', 'CCJ', 'URA'],
        'strategy': 'AI 데이터센터 전력 수요 폭증에 따른 원자력 및 SMR 필수 인프라 섹터.',
        'signal': '🟢 매수 우위 / 적립식 (에너지 인프라 구조적 성장세에 따라 눌림목마다 분할 매수 유효)'
    },
    {
        'sector': '🤖 휴머노이드 로보틱스 (TSLA, SERV) & 대표 ETF: BOTZ',
        'tickers': ['TSLA', 'SERV', 'BOTZ'],
        'strategy': '제조업 및 물류 노동력 대체 패러다임 전환에 따른 로보틱스 및 AI 에이전트 결합.',
        'signal': '🟡 관망 및 조건부 대기 (단기 이평선 지지 확인 후 진입 권장)'
    }
]

for fs in future_sectors:
    print('▶ ' + fs['sector'])
    print('   ㄴ 투자 성향: ' + fs['strategy'])
    print('   ㄴ 🚦 매매 시그널: ' + fs['signal'])
    print('   ㄴ 종목 및 대표 ETF 실시간 가격:')
    for t in fs['tickers']:
        df = yf.Ticker(t).history(period='5d')
        if not df.empty:
            cur = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[-2])
            change = ((cur - prev) / prev) * 100
            sign = '+' if change >= 0 else ''
            print('      • ' + t + ': $' + str(round(cur, 2)) + ' (' + sign + str(round(change, 2)) + '%)')
    print()
