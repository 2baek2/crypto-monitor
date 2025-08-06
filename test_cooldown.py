#!/usr/bin/env python3
"""
쿨다운 시스템 테스트
"""
import asyncio
import time
from crypto_monitor import CryptoMonitor

async def test_cooldown():
    """쿨다운 시스템이 제대로 작동하는지 테스트"""
    monitor = CryptoMonitor()
    
    print("🧪 쿨다운 시스템 테스트 시작...")
    
    # 테스트용 설정: 쿨다운을 1분으로 단축
    test_conditions = {
        'divergence_conditions': {
            'enabled': True,
            'timeframes': ['5m'],
            'rsi_period': 14,
            'lookback_range': [5, 60],
            'include_hidden': True,
            'recent_bars_only': 10,  # 더 많은 최근 봉 확인
            'cooldown_minutes': 1    # 1분 쿨다운
        }
    }
    
    test_symbols = ['BTC_USDT', 'ETH_USDT']
    
    print("🔍 첫 번째 검사...")
    
    # 실제 ticker 데이터 가져오기
    if monitor.market_type == 'futures':
        all_tickers = await monitor.get_top_volume_pairs(limit=50)
    else:
        all_tickers = await monitor.get_top_volume_pairs(limit=50)
    
    # 테스트 심볼들의 ticker 찾기
    test_tickers = []
    for ticker in all_tickers:
        symbol = getattr(ticker, 'contract' if monitor.market_type == 'futures' else 'currency_pair', '')
        if symbol in test_symbols:
            test_tickers.append((ticker, symbol))
    
    # 다이버전스 조건만 테스트
    first_results = {}
    for ticker, symbol in test_tickers:
        # 직접 다이버전스 조건만 확인
        alerts = []
        try:
            div_config = test_conditions['divergence_conditions']
            if div_config.get('enabled', False):
                div_timeframes = div_config.get('timeframes', ['5m'])
                rsi_period = div_config.get('rsi_period', 14)
                lookback_range = tuple(div_config.get('lookback_range', [5, 60]))
                include_hidden = div_config.get('include_hidden', False)
                recent_bars_only = div_config.get('recent_bars_only', 5)
                cooldown_minutes = div_config.get('cooldown_minutes', 30)
                
                for timeframe in div_timeframes:
                    divergence_alerts = monitor.technical_analyzer.detect_rsi_divergence(
                        symbol, timeframe, rsi_period, lookback_range, recent_bars_only
                    )
                    
                    # Hidden 다이버전스 필터링
                    if not include_hidden:
                        divergence_alerts = [
                            alert for alert in divergence_alerts 
                            if "Hidden" not in alert
                        ]
                    
                    if divergence_alerts:
                        # 쿨다운 확인
                        for divergence_msg in divergence_alerts:
                            # 다이버전스 타입 추출
                            div_type = "unknown"
                            if "Regular Bullish" in divergence_msg:
                                div_type = "regular_bullish"
                            elif "Regular Bearish" in divergence_msg:
                                div_type = "regular_bearish"
                            elif "Hidden Bullish" in divergence_msg:
                                div_type = "hidden_bullish"
                            elif "Hidden Bearish" in divergence_msg:
                                div_type = "hidden_bearish"
                            
                            # 쿨다운 키 생성
                            cooldown_key = f"{symbol}_{timeframe}_{rsi_period}_{div_type}"
                            current_time = time.time()
                            
                            # 쿨다운 확인
                            if cooldown_key in monitor.divergence_alert_cache:
                                last_alert_time = monitor.divergence_alert_cache[cooldown_key].timestamp()
                                time_diff = (current_time - last_alert_time) / 60  # 분 단위
                                
                                if time_diff < cooldown_minutes:
                                    print(f"  🕒 {symbol} 쿨다운 중: {time_diff:.1f}분 경과")
                                    continue
                            
                            # 쿨다운이 지났거나 첫 번째 알림인 경우
                            alerts.append(divergence_msg)
                            from datetime import datetime
                            monitor.divergence_alert_cache[cooldown_key] = datetime.now()
                            
        except Exception as e:
            print(f"❌ {symbol} 테스트 오류: {e}")
        
        first_results[symbol] = alerts
        if alerts:
            print(f"📢 {symbol}: {len(alerts)}개 알림")
            for alert in alerts[:1]:  # 처음 1개만 출력
                print(f"  - {alert}")
        else:
            print(f"✅ {symbol}: 다이버전스 없음")
    
    print(f"\n💤 30초 대기 (쿨다운 테스트)...")
    time.sleep(30)
    
    print("🔍 두 번째 검사 (쿨다운 중이어야 함)...")
    second_results = {}
    for ticker, symbol in test_tickers:
        alerts = monitor.check_conditions(ticker, symbol)
        second_results[symbol] = alerts
        if alerts:
            print(f"❌ 쿨다운 실패: {symbol}에서 {len(alerts)}개 알림 발견")
        else:
            print(f"✅ {symbol}: 쿨다운 작동 중 (또는 원래 다이버전스 없음)")
    
    # 원래 설정 복원
    monitor.conditions = original_conditions
    
    # 결과 비교
    print(f"\n� 결과 분석:")
    for symbol in test_symbols:
        if symbol in first_results and symbol in second_results:
            first_count = len(first_results[symbol])
            second_count = len(second_results[symbol])
            print(f"  {symbol}: 첫 번째 {first_count}개 → 두 번째 {second_count}개")
            if first_count > 0 and second_count == 0:
                print(f"  ✅ {symbol}: 쿨다운 정상 작동")
            elif first_count > 0 and second_count > 0:
                print(f"  ❌ {symbol}: 쿨다운 미작동")
            else:
                print(f"  ℹ️ {symbol}: 원래 다이버전스 없음")
    
    print("✨ 쿨다운 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_cooldown())
