#!/usr/bin/env python3
"""
Futures 시장 지원이 추가된 crypto monitor 테스트 스크립트
"""

import asyncio
import logging
from crypto_monitor import CryptoMonitor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_futures_monitor():
    """Futures 모니터링 테스트"""
    print("🚀 Futures 시장 모니터링 테스트 시작...")
    
    try:
        # CryptoMonitor 인스턴스 생성
        monitor = CryptoMonitor()
        
        print(f"📊 시장 타입: {monitor.market_type}")
        print(f"📈 거래 대금 상위 {monitor.market_settings['top_volume_limit']}개 조회")
        
        # 상위 거래 대금 종목 조회 테스트
        print("\n1️⃣ 상위 거래 대금 종목 조회 중...")
        top_symbols = await monitor.get_top_volume_pairs()
        print(f"✅ {len(top_symbols)}개 종목 조회 완료")
        
        # 처음 5개 종목 출력
        print("\n📋 상위 5개 종목:")
        for i, symbol in enumerate(top_symbols[:5], 1):
            print(f"  {i}. {symbol}")
            
        # 조건 확인 테스트 (첫 3개 종목만)
        print(f"\n2️⃣ 조건 확인 테스트 (상위 3개 종목)...")
        test_symbols = top_symbols[:3]
        
        all_alerts = []
        for i, ticker_data in enumerate(test_symbols, 1):
            try:
                # futures ticker는 객체이므로 contract 속성으로 접근
                if hasattr(ticker_data, 'contract'):
                    symbol = ticker_data.contract
                else:
                    symbol = str(ticker_data)
                    
                print(f"  {i}. {symbol} 조건 확인 중...")
                
                # 개별 ticker에 대해 조건 확인
                alerts = monitor.check_conditions(ticker_data, symbol)
                
                if alerts:
                    print(f"    🚨 {len(alerts)}개 알림:")
                    for alert in alerts[:2]:  # 최대 2개만 출력
                        print(f"      - {alert}")
                    all_alerts.extend(alerts)
                else:
                    print(f"    ✅ 조건에 맞는 알림 없음")
                    
            except Exception as e:
                print(f"    ❌ 오류: {e}")
                import traceback
                traceback.print_exc()
        
        if all_alerts:
            print(f"\n� 총 {len(all_alerts)}개 알림 발생!")
        else:
            print(f"\n✅ 현재 조건에 맞는 알림이 없습니다.")
            
        print(f"\n✨ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_futures_monitor())
