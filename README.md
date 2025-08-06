# 🚀 Crypto RSI Monitor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Gate.io API를 활용하여 암호화폐 시장을 모니터링하고, RSI 기술적 분석과 설정된 조건에 맞는 종목이 발견되면 텔레그램으로 알림을 보내는 시스템입니다.

## ✨ 주요 기능

- 🔥 **거래량/거래대금 상위 종목 실시간 모니터링** (Spot/Futures 지원)
- 📊 **사용자 정의 관심종목 모니터링**
- 📈 **RSI 기술적 분석** (5분봉, 15분봉)
- 🎯 **RSI 다이버전스 감지** (Pine Script 알고리즘 기반)
- 💹 **가격 변동률 및 거래량 조건 확인**
- 📱 **텔레그램 실시간 알림** (HTML 안전 처리)
- ⏰ **중복 알림 방지** (쿨다운 시스템)

### 🎯 RSI 기술적 분석

- **지원 시간대**: 5분봉, 15분봉
- **RSI 기간**: 7, 14, 21
- **과매도 신호**: RSI ≤ 30 (매수 타이밍)
- **과매수 신호**: RSI ≥ 70 (매도 타이밍)

### 🔍 RSI 다이버전스 감지

- **Regular Bullish**: 가격 Lower Low + RSI Higher Low (강한 매수 신호)
- **Regular Bearish**: 가격 Higher High + RSI Lower High (강한 매도 신호)  
- **Hidden Bullish**: 가격 Higher Low + RSI Lower Low (상승 추세 지속)
- **Hidden Bearish**: 가격 Lower High + RSI Higher High (하락 추세 지속)
- **스마트 필터링**: 최근 5봉에서 발생한 다이버전스만 감지
- **쿨다운 시스템**: 30분간 동일 신호 중복 방지

## 🛠️ 설치

### 1. 저장소 클론

```bash
git clone https://github.com/[your-username]/crypto-rsi-monitor.git
cd crypto-rsi-monitor
```

### 2. Python 가상환경 생성 및 활성화

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 설정 파일 생성

```bash
cp config.example.py config.py
```

## ⚙️ 설정

### 📱 Telegram Bot 설정 (필수)

1. **Bot 생성**:

   - Telegram에서 [@BotFather](https://t.me/botfather)와 대화
   - `/newbot` 명령어로 새 봇 생성
   - 봇 토큰을 받아 `config.py`에 입력

2. **Chat ID 확인**:
   - 생성한 봇과 대화 시작 (`/start` 전송)
   - `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` 접속
   - JSON에서 `chat.id` 값을 확인하여 `config.py`에 입력

### 🔧 config.py 설정

```python
# Telegram Bot 설정 (필수)
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

# Gate.io API 설정 (선택사항 - 공개 데이터만 사용)
GATE_API_KEY = "your_api_key_here"      # 비워둬도 됨
GATE_API_SECRET = "your_api_secret_here"  # 비워둬도 됨

# 시장 설정
MARKET_SETTINGS = {
    "market_type": "futures",           # "spot" 또는 "futures"
    "top_volume_limit": 30             # 모니터링할 상위 종목 수
}

# RSI 모니터링 조건
MONITOR_CONDITIONS = {
    "rsi_conditions": {
        "enabled": True,
        "timeframes": ["5m", "15m"],    # 모니터링할 시간대
        "periods": [7, 14, 21],         # RSI 계산 기간
        "oversold": 30,                 # 과매도 기준
        "overbought": 70                # 과매수 기준
    },
    
    # RSI 다이버전스 감지 (Pine Script 알고리즘)
    "divergence_conditions": {
        "enabled": True,
        "timeframes": ["5m", "15m"],    # 다이버전스 분석 시간대
        "rsi_period": 14,               # RSI 계산 기간
        "lookback_range": [5, 60],      # 피벗 포인트 검색 범위
        "include_hidden": False,        # Hidden 다이버전스 포함 여부
        "recent_bars_only": 5,          # 최근 N봉에서만 감지
        "cooldown_minutes": 30          # 중복 알림 방지 (분)
    }
    # 기타 조건들...
}
```

## 🚀 사용법

### 빠른 설정 및 테스트

```bash
# 자동 설정 도우미
python setup.py

# 기본 시스템 테스트
python test.py

# RSI 분석 테스트
python test_rsi.py

# RSI 다이버전스 테스트
python test_divergence.py

# 쿨다운 시스템 테스트
python test_simple_cooldown.py
```

### 모니터링 실행

```bash
# 한 번만 실행 (테스트용)
python crypto_monitor.py once

# 지속적 모니터링 시작
python crypto_monitor.py
```

## 📊 알림 예시

### RSI 과매도/과매수 알림

```
🚨 RSI 알림: ASP_USDT

ASP (ASP_USDT)
💰 현재가: $0.152400
📊 24h 변동률: +5.90%
📈 24h 최고: $0.165000
📉 24h 최저: $0.145000
💹 24h 거래량: $2,345,678

조건 충족:
• 📉 5m 과매도 신호: RSI(7): 12.64, RSI(14): 23.76
• 📉 15m 과매도 신호: RSI(7): 22.66

⏰ 시간: 2024-01-15 14:30:00
```

### RSI 다이버전스 알림

```
🚨 다이버전스 알림: BTC_USDT

BTC (BTC_USDT)
💰 현재가: $42,350.00
📊 24h 변동률: -2.15%

조건 충족:
• 🟢 Regular Bullish Divergence (5m): 가격 42180.50 ↓ 42285.75, RSI 28.45 ↑ 25.12
• 🟡 Hidden Bullish Divergence (15m): 가격 42280.00 ↑ 42180.50, RSI 32.15 ↓ 35.82

⏰ 시간: 2024-01-15 14:45:00
```

## 📁 프로젝트 구조

```
crypto-rsi-monitor/
├── crypto_monitor.py          # 🎯 메인 모니터링 스크립트
├── technical_analysis.py      # 📈 RSI 기술적 분석 모듈
├── config.py                  # ⚙️ 설정 파일 (gitignore)
├── config.example.py          # 📋 설정 예시 파일
├── watchlist.py              # 📝 관심종목 리스트
├── setup.py                  # 🛠️ 초기 설정 도우미
├── test*.py                  # 🧪 다양한 테스트 스크립트
├── requirements.txt          # 📦 필요한 패키지 목록
└── README.md                 # 📖 사용 설명서
```

## 🧪 테스트 명령어

```bash
python test.py                    # 전체 시스템 테스트
python test_rsi.py               # RSI 분석 기능 테스트
python test_rsi_signals.py       # RSI 신호 검색 테스트
python test_telegram_rsi.py      # 텔레그램 RSI 알림 테스트
```

## ⚠️ 주의사항

- **투자 참고용**: 이 시스템은 정보 제공 목적이며, 투자 결정의 책임은 사용자에게 있습니다
- **API 제한**: Gate.io API 요청 제한을 고려하여 체크 간격을 적절히 설정하세요
- **개인정보 보호**: API 키와 텔레그램 토큰을 안전하게 보관하세요

## 🤝 기여

이슈 제기, 기능 제안, 풀 리퀘스트를 환영합니다!

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!

## 설치 및 설정

### 1. 필요한 패키지가 이미 설치되어 있습니다:

- gate-api (Gate.io API 클라이언트)
- requests (HTTP 요청)
- python-telegram-bot (텔레그램 봇)
- pandas (데이터 처리)
- numpy (수치 연산)
- ta (기술적 분석 지표)

### 2. API 키 설정

`config.py` 파일을 편집하여 다음 정보를 입력하세요:

```python
# Gate.io API 설정 (공개 API만 사용하는 경우 빈 문자열로 두어도 됩니다)
GATE_API_KEY = "your_gate_api_key_here"
GATE_API_SECRET = "your_gate_api_secret_here"

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"
```

### 3. Telegram Bot 설정 방법

1. **Bot 생성**:

   - Telegram에서 @BotFather와 대화
   - `/newbot` 명령어 입력
   - 봇 이름과 사용자명 설정
   - 받은 토큰을 `TELEGRAM_BOT_TOKEN`에 입력

2. **Chat ID 확인**:
   - 생성한 봇과 대화 시작
   - https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates 에 접속
   - 받은 JSON에서 `chat.id` 값을 `TELEGRAM_CHAT_ID`에 입력

### 4. 관심종목 설정

`watchlist.py` 파일을 편집하여 모니터링하고 싶은 종목을 추가하세요:

```python
WATCHLIST = {
    "BTC_USDT": {
        "name": "Bitcoin",
        "description": "비트코인"
    },
    # 추가 종목...
}
```

### 5. 모니터링 조건 설정

`config.py`에서 알림 조건을 설정하세요:

```python
MONITOR_CONDITIONS = {
    "price_change_24h_percent": {
        "min": -10,  # 24시간 가격 변동률이 -10% 이하일 때 알림
        "max": 15    # 24시간 가격 변동률이 15% 이상일 때 알림
    },
    "volume_change_24h": {
        "min": 1.5   # 거래량이 1.5배 이상 증가했을 때 알림
    },
    "rsi_conditions": {
        "enabled": True,              # RSI 모니터링 활성화
        "timeframes": ["5m", "15m"],  # 5분봉, 15분봉
        "periods": [7, 14, 21],       # RSI 계산 기간
        "oversold": 30,               # 과매도 기준 (RSI ≤ 30)
        "overbought": 70              # 과매수 기준 (RSI ≥ 70)
    }
}
```

## 추가 테스트 명령어

### RSI 분석 테스트

```bash
python test_rsi.py              # RSI 계산 및 분석 테스트
python test_rsi_signals.py      # RSI 신호 검색 테스트
python test_telegram_rsi.py     # 텔레그램 RSI 알림 테스트
```

## 사용법

### 1. 한 번만 실행 (테스트용)

```bash
python crypto_monitor.py once
```

### 2. 지속적 모니터링 (실제 운영)

```bash
python crypto_monitor.py
```

## 파일 구조

- `crypto_monitor.py`: 메인 모니터링 스크립트
- `config.py`: API 키 및 설정 파일
- `watchlist.py`: 모니터링할 종목 리스트
- `technical_analysis.py`: RSI 기술적 분석 모듈
- `test.py`: 기본 시스템 테스트
- `test_rsi.py`: RSI 분석 기능 테스트
- `test_rsi_signals.py`: RSI 신호 검색 테스트
- `test_telegram_rsi.py`: 텔레그램 RSI 알림 테스트
- `crypto_monitor.log`: 로그 파일 (실행 후 생성)

## 알림 예시

### 💰 가격 변동 알림

```
🚨 알림: BTC_USDT

Bitcoin (BTC_USDT)
💰 현재가: $45,123.45
📊 24h 변동률: -12.34%
📈 24h 최고: $48,500.00
📉 24h 최저: $44,800.00
💹 24h 거래량: $1,234,567,890

조건 충족:
• 📉 24시간 가격 변동률: -12.34% (임계값: -10% 이하)

⏰ 시간: 2024-01-15 14:30:00
```

### 📈 RSI 기술적 분석 알림

```
🚨 RSI 알림: ASP_USDT

ASP (ASP_USDT)
💰 현재가: $0.152400
📊 24h 변동률: +5.90%
📈 24h 최고: $0.165000
📉 24h 최저: $0.145000
💹 24h 거래량: $2,345,678

조건 충족:
• 📉 5m 과매도 신호: RSI(7): 12.64, RSI(14): 23.76
• 📉 15m 과매도 신호: RSI(7): 22.66

⏰ 시간: 2024-01-15 14:30:00
```

## 주의사항

1. **API 제한**: Gate.io API는 분당 요청 제한이 있으므로 체크 간격을 너무 짧게 설정하지 마세요.
2. **개인정보 보호**: API 키와 텔레그램 토큰을 안전하게 보관하세요.
3. **투자 주의**: 이 시스템은 정보 제공용이며, 투자 결정의 책임은 사용자에게 있습니다.

## 문제 해결

### 일반적인 오류들:

1. **Gate.io API 오류**: API 키 확인 또는 네트워크 연결 확인
2. **Telegram 오류**: 봇 토큰과 Chat ID 확인
3. **모듈 없음 오류**: pip install 명령어로 패키지 재설치

로그 파일(`crypto_monitor.log`)을 확인하여 자세한 오류 정보를 확인할 수 있습니다.
