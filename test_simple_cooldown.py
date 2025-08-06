#!/usr/bin/env python3
"""
쿨다운 시스템 간단 테스트
"""
import asyncio
import time
from datetime import datetime
from crypto_monitor import CryptoMonitor

async def simple_cooldown_test():
    """간단한 쿨다운 테스트"""
    monitor = CryptoMonitor()
    
    print("🧪 쿨다운 시스템 간단 테스트...")
    print("📊 현재 쿨다운 캐시 상태:")
    print(f"  - 캐시 크기: {len(monitor.divergence_alert_cache)}")
    
    # 테스트용 가짜 알림 추가
    test_key = "BTC_USDT_5m_14_regular_bullish"
    monitor.divergence_alert_cache[test_key] = datetime.now()
    
    print(f"  - 테스트 키 추가: {test_key}")
    print(f"  - 현재 시간: {datetime.now()}")
    
    # 30초 후 캐시 확인
    print("\n💤 30초 대기...")
    time.sleep(30)
    
    if test_key in monitor.divergence_alert_cache:
        last_time = monitor.divergence_alert_cache[test_key]
        time_diff = (datetime.now() - last_time).total_seconds() / 60
        print(f"✅ 캐시에서 발견: {time_diff:.2f}분 경과")
        
        if time_diff < 1:  # 1분 미만
            print("✅ 쿨다운 작동 중")
        else:
            print("❌ 쿨다운 만료")
    else:
        print("❌ 캐시에서 찾을 수 없음")
    
    print("✨ 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(simple_cooldown_test())
