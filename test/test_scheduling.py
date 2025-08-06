#!/usr/bin/env python3
"""
스마트 스케줄링 테스트
"""
import sys
import os
# 상위 디렉터리(프로젝트 루트)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from datetime import datetime
from crypto_monitor import CryptoMonitor

def test_scheduling():
    """스케줄링 로직 테스트"""
    monitor = CryptoMonitor()
    
    print("🕐 스마트 스케줄링 테스트")
    print(f"📅 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 타임프레임 변환 테스트
    print("\n🔄 타임프레임 변환 테스트:")
    test_timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"]
    for tf in test_timeframes:
        minutes = monitor.timeframe_to_minutes(tf)
        print(f"  {tf} → {minutes}분")
    
    # 가장 작은 타임프레임 찾기
    smallest_tf = monitor.get_smallest_timeframe_minutes()
    print(f"\n📊 설정된 가장 작은 타임프레임: {smallest_tf}분")
    
    # 다음 봉 마감 시간 계산
    for tf_minutes in [5, 15, 30, 60]:
        next_time = monitor.get_next_candle_close_time(tf_minutes)
        wait_seconds = (next_time - datetime.now()).total_seconds()
        print(f"  {tf_minutes}분봉 다음 마감: {next_time.strftime('%H:%M:%S')} ({wait_seconds:.0f}초 후)")
    
    # 실제 스케줄링 시뮬레이션
    print(f"\n🚀 실제 스케줄링 시뮬레이션:")
    print(f"1. 시작 시 즉시 실행")
    
    next_candle_time = monitor.get_next_candle_close_time(smallest_tf)
    wait_seconds = (next_candle_time - datetime.now()).total_seconds()
    print(f"2. {smallest_tf}분봉 마감까지 {wait_seconds:.0f}초 대기")
    print(f"   다음 실행: {next_candle_time.strftime('%H:%M:%S')}")
    print(f"3. 그 후 30분마다 정기 실행")
    
    print("\n✨ 스케줄링 테스트 완료!")

if __name__ == "__main__":
    test_scheduling()
