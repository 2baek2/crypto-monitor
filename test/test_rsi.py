#!/usr/bin/env python3
"""
RSI 분석 테스트 스크립트
"""

import asyncio
import sys
import os
# 상위 디렉터리(프로젝트 루트)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from technical_analysis import TechnicalAnalyzer
from crypto_monitor import CryptoMonitor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rsi_analysis():
    """RSI 분석을 테스트합니다."""
    print("=== RSI 분석 테스트 ===")
    
    monitor = CryptoMonitor()
    analyzer = monitor.technical_analyzer
    
    # 테스트할 종목들
    test_symbols = ["BTC_USDT", "ETH_USDT", "BNB_USDT"]
    timeframes = ["5m", "15m"]
    periods = [7, 14, 21]
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol} RSI 분석:")
        
        try:
            # 각 시간대별로 RSI 분석
            for timeframe in timeframes:
                print(f"\n  {timeframe} 차트:")
                
                # 캔들스틱 데이터 가져오기
                df = analyzer.get_candlestick_data(symbol, timeframe, limit=100)
                
                if df is None:
                    print(f"    ❌ {timeframe} 데이터를 가져올 수 없습니다.")
                    continue
                
                print(f"    📈 데이터: {len(df)}개 캔들")
                print(f"    💰 현재가: ${df['close'].iloc[-1]:,.6f}")
                
                # RSI 계산
                rsi_values = analyzer.calculate_rsi(df, periods)
                
                if rsi_values:
                    for period in sorted(periods):
                        rsi_key = f'rsi_{period}'
                        if rsi_key in rsi_values:
                            rsi_value = rsi_values[rsi_key]
                            status = ""
                            
                            if rsi_value <= 30:
                                status = " (과매도 🔴)"
                            elif rsi_value >= 70:
                                status = " (과매수 🟢)"
                            else:
                                status = " (중립 ⚪)"
                            
                            print(f"    🔸 RSI({period}): {rsi_value}{status}")
                else:
                    print(f"    ❌ RSI 계산 실패")
            
            # RSI 조건 확인 테스트
            print(f"\n  🚨 알림 조건 확인:")
            rsi_alerts = analyzer.analyze_rsi_conditions(
                symbol, timeframes, periods, oversold=30, overbought=70
            )
            
            if rsi_alerts:
                for alert in rsi_alerts:
                    print(f"    • {alert}")
            else:
                print(f"    ✅ 현재 RSI 조건에 맞지 않습니다.")
                
        except Exception as e:
            print(f"    ❌ 오류 발생: {e}")
            
        print("-" * 50)


async def test_full_monitoring():
    """전체 모니터링 시스템 테스트 (RSI 포함)"""
    print("\n=== 전체 모니터링 테스트 (RSI 포함) ===")
    
    monitor = CryptoMonitor()
    
    # BTC만 테스트
    test_symbol = "BTC_USDT"
    
    try:
        # 티커 정보 가져오기
        tickers = monitor.spot_api.list_tickers(currency_pair=test_symbol)
        
        if tickers:
            ticker = tickers[0]
            print(f"\n📊 {test_symbol} 종합 분석:")
            print(monitor.format_ticker_info(ticker))
            
            # 모든 조건 확인 (RSI 포함)
            alerts = monitor.check_conditions(ticker, test_symbol)
            
            if alerts:
                print(f"\n🚨 알림 조건 충족 ({len(alerts)}개):")
                for i, alert in enumerate(alerts, 1):
                    print(f"  {i}. {alert}")
            else:
                print(f"\n✅ 현재 설정된 모든 조건에 맞지 않습니다.")
                
        else:
            print(f"❌ {test_symbol} 티커 정보를 가져올 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def main():
    """메인 테스트 함수"""
    print("🚀 RSI 분석 기능 테스트를 시작합니다...\n")
    
    # 1. RSI 분석 테스트
    await test_rsi_analysis()
    
    print("\n" + "="*70 + "\n")
    
    # 2. 전체 시스템 테스트
    await test_full_monitoring()
    
    print(f"\n🎉 RSI 분석 테스트가 완료되었습니다!")
    print("\n설정 정보:")
    print("- RSI 기간: 7, 14, 21")
    print("- 시간대: 5분봉, 15분봉")
    print("- 과매도: RSI ≤ 30")
    print("- 과매수: RSI ≥ 70")
    print("\nconfig.py에서 RSI 조건을 조정할 수 있습니다.")


if __name__ == "__main__":
    asyncio.run(main())
