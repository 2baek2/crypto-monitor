#!/usr/bin/env python3
"""
한국시간 기반 알림 스케줄링 시스템 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from crypto_monitor import CryptoMonitor
from datetime import datetime
import pytz

def test_notification_scheduling():
    """알림 스케줄링 기능 테스트"""
    
    # CryptoMonitor 인스턴스 생성
    monitor = CryptoMonitor()
    
    # 한국시간 설정
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz)
    
    print(f"현재 한국시간: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"현재 요일: {now.strftime('%A')}")
    print(f"현재 시각: {now.hour:02d}:{now.minute:02d}")
    
    # 현재 시간 알림 허용 상태 확인
    is_allowed = monitor.is_notification_allowed()
    print(f"\n현재 시각 알림 허용 여부: {'✅ 허용' if is_allowed else '❌ 차단'}")
    
    # 다양한 시간대 테스트
    test_times = [
        (7, 30),   # 아침 7:30 - 차단되어야 함 (08:00 이전)
        (8, 30),   # 아침 8:30 - 허용되어야 함
        (12, 0),   # 낮 12:00 - 허용되어야 함
        (18, 0),   # 저녁 6:00 - 허용되어야 함
        (21, 30),  # 저녁 9:30 - 허용되어야 함
        (22, 30),  # 밤 10:30 - 차단되어야 함 (22:00 이후)
        (23, 59),  # 밤 11:59 - 차단되어야 함
        (1, 0),    # 새벽 1:00 - 차단되어야 함
    ]
    
    print("\n=== 시간대별 알림 허용 상태 테스트 ===")
    for hour, minute in test_times:
        # 테스트용 시간 생성
        test_time = now.replace(hour=hour, minute=minute)
        
        # 테스트용 시간으로 알림 허용 여부 확인
        # (실제로는 현재 시간을 사용하지만, 테스트를 위해 임시로 수정)
        original_method = monitor.is_notification_allowed
        
        def test_is_notification_allowed():
            from config import NOTIFICATION_SCHEDULE
            
            if not NOTIFICATION_SCHEDULE.get('enabled', True):
                return True
            
            korea_tz = pytz.timezone(NOTIFICATION_SCHEDULE.get('timezone', 'Asia/Seoul'))
            current_time = test_time  # 테스트용 시간 사용
            
            current_hour = current_time.hour
            current_weekday = current_time.weekday()  # 0=월요일, 6=일요일
            
            # 주말 여부 확인 (토요일=5, 일요일=6)
            is_weekend = current_weekday >= 5
            
            # 주말 알림 비활성화 설정 확인
            if is_weekend and NOTIFICATION_SCHEDULE.get('disable_weekends', False):
                return False
            
            # 조용한 시간 설정
            quiet_hours = NOTIFICATION_SCHEDULE.get('quiet_hours', {})
            
            # 주말 전용 조용한 시간 설정이 있고 활성화된 경우
            if is_weekend:
                weekend_quiet = NOTIFICATION_SCHEDULE.get('weekend_quiet_hours', {})
                if weekend_quiet.get('enabled', False):
                    quiet_hours = weekend_quiet
            
            # 시간 파싱 (HH:MM 형식에서 시간만 추출)
            start_time_str = quiet_hours.get('start', '22:00')
            end_time_str = quiet_hours.get('end', '08:00')
            start_hour = int(start_time_str.split(':')[0])
            end_hour = int(end_time_str.split(':')[0])
            
            # 시간 비교 (start_hour가 end_hour보다 큰 경우 다음날까지 처리)
            if start_hour <= end_hour:
                # 같은 날 내 시간대 (예: 08시 ~ 22시 허용)
                is_quiet_time = start_hour <= current_hour <= end_hour
                is_allowed = not is_quiet_time
            else:
                # 다음날로 넘어가는 시간대 (예: 22시 ~ 08시 조용)
                is_quiet_time = current_hour >= start_hour or current_hour < end_hour
                is_allowed = not is_quiet_time
            
            return is_allowed
        
        # 테스트 실행
        result = test_is_notification_allowed()
        status = "✅ 허용" if result else "❌ 차단"
        print(f"{hour:02d}:{minute:02d} - {status}")
    
    print("\n=== 주말 설정 테스트 ===")
    # 주말에 대한 특별 설정이 있는지 확인
    from config import NOTIFICATION_SCHEDULE
    
    weekend_quiet = NOTIFICATION_SCHEDULE.get('weekend_quiet_hours', {})
    weekend_enabled = weekend_quiet.get('enabled', False)
    if weekend_enabled:
        weekend_start = weekend_quiet.get('start', '22:00')
        weekend_end = weekend_quiet.get('end', '08:00')
        print(f"주말 금지 시간: {weekend_start} ~ {weekend_end}")
    else:
        print("주말 특별 설정 없음 (평일과 동일)")
    
    quiet_hours = NOTIFICATION_SCHEDULE.get('quiet_hours', {})
    weekday_start = quiet_hours.get('start', '22:00')
    weekday_end = quiet_hours.get('end', '08:00')
    print(f"평일 금지 시간: {weekday_start} ~ {weekday_end}")

if __name__ == "__main__":
    print("🔔 한국시간 기반 알림 스케줄링 시스템 테스트")
    print("=" * 50)
    test_notification_scheduling()
