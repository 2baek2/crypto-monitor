#!/usr/bin/env python3
"""
Futures 시장 실제 모니터링 실행 스크립트
"""

import asyncio
import logging
from crypto_monitor import CryptoMonitor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """실제 모니터링 실행"""
    print("🚀 암호화폐 Futures 모니터링을 시작합니다...")
    
    try:
        monitor = CryptoMonitor()
        
        print(f"📊 시장 타입: {monitor.market_type}")
        print(f"📈 모니터링 대상: 거래 대금 상위 {monitor.market_settings['top_volume_limit']}개")
        print(f"⏱️  체크 주기: {monitor.market_settings.get('check_interval', 3)}분")
        print(f"🔔 최대 알림: 주기당 {monitor.market_settings['max_alerts_per_cycle']}개")
        print("\n모니터링 조건:")
        print("- RSI 과매도: ≤30, 과매수: ≥70")
        print("- RSI 기간: 7, 14, 21")
        print("- 타임프레임: 5분봉, 15분봉")
        
        print("\n🎯 모니터링 시작! (Ctrl+C로 중단)")
        
        # 연속 모니터링 시작
        await monitor.run_continuous_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️  모니터링이 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
