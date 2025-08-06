#!/usr/bin/env python3
"""
RSI 다이버전스 테스트 스크립트
"""

import asyncio
import logging
from technical_analysis import TechnicalAnalyzer
import gate_api

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_divergence():
    """RSI 다이버전스 테스트"""
    print("🔍 RSI 다이버전스 분석 테스트 시작...")
    
    try:
        # Gate.io API 설정
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4"
        )
        api_client = gate_api.ApiClient(configuration)
        spot_api = gate_api.SpotApi(api_client)
        futures_api = gate_api.FuturesApi(api_client)
        
        # TechnicalAnalyzer 초기화 (futures 모드)
        analyzer = TechnicalAnalyzer(
            spot_api=spot_api,
            futures_api=futures_api,
            market_type='futures'
        )
        
        # 테스트할 심볼들
        test_symbols = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']
        timeframes = ['5m', '15m']
        
        print(f"🎯 테스트 대상: {', '.join(test_symbols)}")
        print(f"⏰ 타임프레임: {', '.join(timeframes)}")
        
        for symbol in test_symbols:
            print(f"\n📊 {symbol} 다이버전스 분석 중...")
            
            for timeframe in timeframes:
                try:
                    divergences = analyzer.detect_rsi_divergence(
                        symbol=symbol,
                        timeframe=timeframe,
                        rsi_period=14,
                        lookback_range=(5, 60)
                    )
                    
                    if divergences:
                        print(f"  🚨 {timeframe}: {len(divergences)}개 다이버전스 발견!")
                        for divergence in divergences:
                            print(f"    {divergence}")
                    else:
                        print(f"  ✅ {timeframe}: 다이버전스 없음")
                        
                except Exception as e:
                    print(f"  ❌ {timeframe}: 오류 - {e}")
        
        print(f"\n✨ 다이버전스 분석 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_divergence())
