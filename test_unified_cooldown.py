#!/usr/bin/env python3
"""
통합 쿨다운 시스템 테스트
"""
import asyncio
import time
from datetime import datetime
from crypto_monitor import CryptoMonitor
from config import ALERT_COOLDOWN

async def test_unified_cooldown():
    """통합 쿨다운 시스템 테스트"""
    monitor = CryptoMonitor()
    
    print("🧪 통합 쿨다운 시스템 테스트")
    print(f"📊 쿨다운 설정:")
    print(f"  - 활성화: {ALERT_COOLDOWN.get('enabled', False)}")
    print(f"  - 쿨다운 시간: {ALERT_COOLDOWN.get('cooldown_minutes', 30)}분")
    print(f"  - 조건별 개별 쿨다운: {ALERT_COOLDOWN.get('per_condition_type', True)}")
    
    print(f"\n🔧 캐시 키 생성 테스트:")
    test_cases = [
        ("BTC_USDT", "rsi_oversold", "5m"),
        ("ETH_USDT", "divergence", "15m_regular_bullish"),
        ("SOL_USDT", "price_drop", "10"),
        ("BTC_USDT", "volume_surge", "2.5"),
    ]
    
    for symbol, condition_type, additional_info in test_cases:
        cache_key = monitor.generate_alert_cache_key(symbol, condition_type, additional_info)
        print(f"  {symbol} + {condition_type} + {additional_info} → {cache_key}")
    
    print(f"\n⏰ 쿨다운 로직 테스트:")
    test_key = "TEST_BTC_USDT_rsi_oversold_5m"
    
    # 첫 번째 확인 (쿨다운 없음)
    is_cooldown1 = monitor.is_alert_in_cooldown(test_key)
    print(f"  첫 번째 확인: {is_cooldown1} (예상: False)")
    
    # 캐시 업데이트
    monitor.update_alert_cache(test_key)
    print(f"  캐시 업데이트: {test_key}")
    
    # 두 번째 확인 (쿨다운 중)
    is_cooldown2 = monitor.is_alert_in_cooldown(test_key)
    print(f"  두 번째 확인: {is_cooldown2} (예상: True)")
    
    # 캐시 상태 출력
    print(f"\n📋 현재 알림 캐시 상태:")
    print(f"  캐시 크기: {len(monitor.alert_cache)}")
    for key, timestamp in monitor.alert_cache.items():
        elapsed = (datetime.now() - timestamp).total_seconds() / 60
        print(f"  - {key}: {timestamp.strftime('%H:%M:%S')} ({elapsed:.1f}분 경과)")
    
    print("\n✨ 통합 쿨다운 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_unified_cooldown())
