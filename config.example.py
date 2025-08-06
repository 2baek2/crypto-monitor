# Gate.io API 설정 (공개 데이터만 사용하는 경우 비워두어도 됩니다)
GATE_API_KEY = "your_gate_api_key_here"
GATE_API_SECRET = "your_gate_api_secret_here"

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"

# 모니터링 설정
# 예시 조건들 - 필요에 따라 수정하세요
MONITOR_CONDITIONS = {
    "price_change_24h_percent": {
        "min": -10,  # 24시간 가격 변동률이 -10% 이하일 때 알림
        "max": 15    # 24시간 가격 변동률이 15% 이상일 때 알림
    },
    "volume_change_24h": {
        "min": 1.5   # 24시간 거래량이 1.5배 이상 증가했을 때 알림
    },
    "rsi_conditions": {
        "enabled": True,                    # RSI 모니터링 활성화
        "timeframes": ["5m", "15m"],        # 5분봉, 15분봉 차트
        "periods": [7, 14, 21],             # RSI 계산 기간
        "oversold": 30,                     # 과매도 기준 (RSI ≤ 30)
        "overbought": 70                    # 과매수 기준 (RSI ≥ 70)
    }
}

# 거래소 및 모니터링 설정
MARKET_SETTINGS = {
    "market_type": "futures",         # "spot" 또는 "futures"
    "settle": "usdt",                # futures 결제 통화 (usdt, btc)
    "top_volume_limit": 50,          # 거래량 상위 몇 개 종목을 모니터링할지
    "max_alerts_per_cycle": 5        # 한 번에 최대 몇 개의 알림을 보낼지
}

# 체크 주기 (분)
CHECK_INTERVAL_MINUTES = 30
