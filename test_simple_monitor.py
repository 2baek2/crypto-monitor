#!/usr/bin/env python3
"""
간단한 모니터링 시스템 테스트 (실제 API 호출 없이)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from crypto_monitor import CryptoMonitor
from datetime import datetime
import pytz

def test_monitor_initialization():
    """모니터 초기화 테스트"""
    try:
        monitor = CryptoMonitor()
        print("✅ CryptoMonitor 초기화 성공")
        
        # 현재 시각 알림 허용 상태 확인
        is_allowed = monitor.is_notification_allowed()
        
        # 한국시간 출력
        korea_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(korea_tz)
        
        print(f"📅 현재 한국시간: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"🔔 현재 알림 허용 상태: {'✅ 허용' if is_allowed else '❌ 차단'}")
        
        # 설정 정보 출력
        from config import NOTIFICATION_SCHEDULE, ALERT_COOLDOWN
        print(f"\n⚙️  알림 설정:")
        
        quiet_hours = NOTIFICATION_SCHEDULE.get('quiet_hours', {})
        start_time = quiet_hours.get('start', '22:00')
        end_time = quiet_hours.get('end', '08:00')
        print(f"   - 한국시간 기준 금지시간: {start_time} ~ {end_time}")
        
        cooldown_minutes = ALERT_COOLDOWN.get('cooldown_minutes', 30)
        print(f"   - 알림 쿨다운: {cooldown_minutes} 분")
        
        weekend_quiet = NOTIFICATION_SCHEDULE.get('weekend_quiet_hours', {})
        weekend_enabled = weekend_quiet.get('enabled', False)
        print(f"   - 주말 특별설정: {'있음' if weekend_enabled else '없음'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🚀 간단한 모니터링 시스템 테스트")
    print("=" * 50)
    test_monitor_initialization()
