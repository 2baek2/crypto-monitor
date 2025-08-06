#!/usr/bin/env python3
"""
수정된 다이버전스 알림 시스템 테스트
"""
import sys
import os
# 상위 디렉터리(프로젝트 루트)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import asyncio
import logging
from crypto_monitor import CryptoMonitor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_telegram_alerts():
    """텔레그램 알림 테스트"""
    print("📲 다이버전스 텔레그램 알림 테스트 시작...")
    
    try:
        monitor = CryptoMonitor()
        
        # 테스트 메시지
        test_messages = [
            "🟢 Regular Bullish Divergence (5m): 가격 113449.0000 ↓ 113708.0000, RSI 37.21 ↑ 36.79",
            "🔴 Regular Bearish Divergence (15m): 가격 115300.0000 ↑ 115031.5000, RSI 58.33 ↓ 65.40",
            "🟡 Hidden Bullish Divergence (5m): 가격 113708.0000 ↑ 113566.3000, RSI 36.79 ↓ 39.10"
        ]
        
        print("📤 테스트 메시지 전송 중...")
        for i, message in enumerate(test_messages, 1):
            test_msg = f"🧪 <b>다이버전스 테스트 {i}/3</b>\n\n{message}"
            
            success = await monitor.send_telegram_message(test_msg)
            if success:
                print(f"  ✅ 메시지 {i} 전송 성공")
            else:
                print(f"  ❌ 메시지 {i} 전송 실패")
            
            await asyncio.sleep(1)  # 메시지 간격
        
        print("\n🎯 실제 모니터링 1회 실행...")
        await monitor.monitor_markets()
        
        print("✨ 텔레그램 알림 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_telegram_alerts())
