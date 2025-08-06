#!/usr/bin/env python3
"""
테스트 실행기 - 모든 테스트를 순차적으로 실행합니다.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_test(test_file, description):
    """개별 테스트를 실행합니다."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"📄 파일: {test_file}")
    print('='*60)
    
    try:
        # uv run 명령어로 테스트 실행
        result = subprocess.run(
            ["uv", "run", "python", str(test_file)],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - 성공")
            return True
        else:
            print(f"❌ {description} - 실패 (코드: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - 오류: {e}")
        return False

def main():
    """메인 테스트 실행기"""
    print("🚀 Crypto Monitor 통합 테스트 시작")
    print(f"📅 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테스트 목록 (순서대로 실행)
    tests = [
        ("test/test.py", "기본 시스템 테스트"),
        ("test/test_rsi.py", "RSI 분석 테스트"),
        ("test/test_divergence.py", "RSI 다이버전스 테스트"),
        ("test/test_scheduling.py", "스마트 스케줄링 테스트"),
        ("test/test_unified_cooldown.py", "통합 쿨다운 시스템 테스트"),
        ("test/test_simple_cooldown.py", "간단한 쿨다운 테스트"),
    ]
    
    # 선택적 테스트 (오류 발생해도 계속)
    optional_tests = [
        ("test/test_futures_monitor.py", "퓨처스 모니터링 테스트"),
        ("test/test_telegram_alerts.py", "텔레그램 알림 테스트"),
    ]
    
    passed = 0
    failed = 0
    
    # 필수 테스트 실행
    print("\n📋 필수 테스트 실행 중...")
    for test_file, description in tests:
        if os.path.exists(test_file):
            if run_test(test_file, description):
                passed += 1
            else:
                failed += 1
            time.sleep(2)  # 테스트 간 간격
        else:
            print(f"⚠️ 테스트 파일 없음: {test_file}")
    
    # 선택적 테스트 실행
    print("\n📋 선택적 테스트 실행 중...")
    for test_file, description in optional_tests:
        if os.path.exists(test_file):
            if run_test(test_file, f"{description} (선택적)"):
                passed += 1
            else:
                print(f"⚠️ {description} 실패 (무시하고 계속)")
            time.sleep(1)
        else:
            print(f"ℹ️ 선택적 테스트 파일 없음: {test_file}")
    
    # 결과 요약
    total = passed + failed
    print(f"\n{'='*60}")
    print("🎯 테스트 결과 요약")
    print('='*60)
    print(f"✅ 성공: {passed}개")
    print(f"❌ 실패: {failed}개")
    print(f"📊 총 테스트: {total}개")
    print(f"📅 완료 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed == 0:
        print("\n🎉 모든 테스트가 성공했습니다!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {failed}개의 테스트가 실패했습니다.")
        print("자세한 내용은 위의 로그를 확인하세요.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 테스트 실행 중 예외 발생: {e}")
        sys.exit(1)
