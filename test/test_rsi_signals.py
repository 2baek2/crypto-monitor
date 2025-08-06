#!/usr/bin/env python3
"""
RSI 조건 테스트를 위한 임시 스크립트
더 민감한 RSI 조건으로 테스트합니다.
"""

import asyncio
import sys
import os
# 상위 디렉터리(프로젝트 루트)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from crypto_monitor import CryptoMonitor
from technical_analysis import TechnicalAnalyzer
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_with_sensitive_rsi():
    """더 민감한 RSI 조건으로 테스트합니다."""
    print("=== 민감한 RSI 조건 테스트 ===")
    print("과매도: RSI ≤ 50, 과매수: RSI ≥ 50")
    
    monitor = CryptoMonitor()
    
    # 거래량 상위 종목들 가져오기
    top_pairs = await monitor.get_top_volume_pairs(10)
    
    if not top_pairs:
        print("❌ 거래량 상위 종목을 가져올 수 없습니다.")
        return
    
    found_signals = 0
    
    for ticker in top_pairs:
        symbol = ticker.currency_pair
        print(f"\n📊 {symbol} RSI 분석:")
        
        try:
            # RSI 조건 확인 (테스트용 민감한 조건)
            rsi_alerts = monitor.technical_analyzer.analyze_rsi_conditions(
                symbol, 
                timeframes=["5m", "15m"], 
                periods=[7, 14, 21], 
                oversold=50,  # 테스트용: 50 이하
                overbought=50  # 테스트용: 50 이상
            )
            
            if rsi_alerts:
                found_signals += 1
                print(f"  🚨 신호 발견!")
                for alert in rsi_alerts:
                    print(f"    • {alert}")
                    
                # 현재가 정보도 표시
                current_price = float(ticker.last)
                change_24h = float(ticker.change_percentage)
                print(f"  💰 현재가: ${current_price:,.6f} ({change_24h:+.2f}%)")
            else:
                print(f"  ✅ 신호 없음")
                
        except Exception as e:
            print(f"  ❌ 오류: {e}")
    
    print(f"\n📈 총 {found_signals}/{len(top_pairs)} 종목에서 RSI 신호 발견")


async def find_extreme_rsi():
    """실제 극단적인 RSI 값을 찾아보겠습니다."""
    print("\n=== 극단적 RSI 값 검색 ===")
    print("RSI 30 이하 또는 70 이상인 종목을 찾습니다...")
    
    monitor = CryptoMonitor()
    
    # 더 많은 종목 검사
    top_pairs = await monitor.get_top_volume_pairs(50)
    
    if not top_pairs:
        print("❌ 종목 데이터를 가져올 수 없습니다.")
        return
    
    extreme_signals = []
    
    for i, ticker in enumerate(top_pairs, 1):
        symbol = ticker.currency_pair
        print(f"\r검사 중... ({i}/{len(top_pairs)}) {symbol}", end="", flush=True)
        
        try:
            # RSI 조건 확인 (실제 조건)
            rsi_alerts = monitor.technical_analyzer.analyze_rsi_conditions(
                symbol, 
                timeframes=["5m", "15m"], 
                periods=[7, 14, 21], 
                oversold=30,   # 실제 과매도
                overbought=70  # 실제 과매수
            )
            
            if rsi_alerts:
                current_price = float(ticker.last)
                change_24h = float(ticker.change_percentage)
                
                extreme_signals.append({
                    'symbol': symbol,
                    'price': current_price,
                    'change_24h': change_24h,
                    'alerts': rsi_alerts
                })
                
        except Exception as e:
            continue
    
    print(f"\n\n🎯 극단적 RSI 신호 결과:")
    
    if extreme_signals:
        print(f"총 {len(extreme_signals)}개 종목에서 극단적 RSI 신호 발견!")
        
        for i, signal in enumerate(extreme_signals, 1):
            print(f"\n{i}. 🚨 {signal['symbol']}")
            print(f"   💰 ${signal['price']:,.6f} ({signal['change_24h']:+.2f}%)")
            for alert in signal['alerts']:
                print(f"   • {alert}")
    else:
        print("현재 극단적 RSI 조건을 만족하는 종목이 없습니다.")
        print("(RSI ≤ 30 또는 RSI ≥ 70)")


async def main():
    """메인 함수"""
    print("🔍 RSI 신호 검색 테스트를 시작합니다...\n")
    
    # 1. 민감한 조건으로 테스트
    await test_with_sensitive_rsi()
    
    print("\n" + "="*70)
    
    # 2. 실제 극단적 RSI 값 검색
    await find_extreme_rsi()
    
    print(f"\n🎉 RSI 신호 검색이 완료되었습니다!")


if __name__ == "__main__":
    asyncio.run(main())
