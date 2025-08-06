# Gate.io API 설정 (공개 데이터만 사용하는 경우 비워두어도 됩니다)
GATE_API_KEY = "your_gate_api_key_here"
GATE_API_SECRET = "your_gate_api_secret_here"

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"

# 모니터링 설정
# 예시 조건들 - 필요에 따라 수정하세요
MONITOR_CONDITIONS = {
    "rsi_conditions": {
        "enabled": True,                    # RSI 모니터링 활성화
        "timeframes": ["5m", "15m"],        # 5분봉, 15분봉 차트
        "periods": [7, 14, 21],             # RSI 계산 기간
        "oversold": 30,                     # 과매도 기준 (RSI ≤ 30)
        "overbought": 70                    # 과매수 기준 (RSI ≥ 70)
    },
    "divergence_conditions": {
        "enabled": True,
        "timeframes": ["5m", "15m"],        # 다이버전스 분석 시간대
        "rsi_period": 14,                   # RSI 계산 기간
        "lookback_range": [5, 60],          # 피벗 포인트 검색 범위
        "include_hidden": False,            # Hidden 다이버전스 포함 여부
        "recent_bars_only": 5               # 최근 N봉에서만 감지
    }
}

# 알림 쿨다운 설정
ALERT_COOLDOWN = {
    "enabled": True,                        # 쿨다운 시스템 활성화
    "cooldown_minutes": 30,                 # 같은 조건에 대한 알림 간격 (분)
    "per_condition_type": True              # 조건 타입별로 개별 쿨다운 적용 (True) 또는 심볼 전체 쿨다운 (False)
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
