#!/usr/bin/env python3
"""
Silent 알림 테스트
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from crypto_monitor import CryptoMonitor

async def test_silent_notification():
    """Silent 알림 테스트"""
    
    monitor = CryptoMonitor()
    
    # 설정 확인
    from config import NOTIFICATION_SCHEDULE
    print(f"NOTIFICATION_SCHEDULE enabled: {NOTIFICATION_SCHEDULE.get('enabled', False)}")
    print(f"조용한 시간 설정: {NOTIFICATION_SCHEDULE.get('quiet_hours', {})}")
    
    # 현재 시간의 알림 허용 상태 확인
    is_allowed = monitor.is_notification_allowed()
    print(f"현재 알림 허용 상태: {'✅ 허용' if is_allowed else '❌ 차단 (silent 모드)'}")
    
    # 테스트 메시지 발송
    test_message = "🧪 Silent 알림 테스트 메시지\n현재 시간에 이 메시지가 무음으로 전송되어야 합니다."
    
    if monitor.bot and monitor.chat_id:
        print("📱 테스트 메시지를 발송합니다...")
        result = await monitor.send_telegram_message(test_message)
        print(f"전송 결과: {'✅ 성공' if result else '❌ 실패'}")
    else:
        print("❌ 텔레그램 설정이 없어 메시지를 보낼 수 없습니다.")

if __name__ == "__main__":
    asyncio.run(test_silent_notification())
