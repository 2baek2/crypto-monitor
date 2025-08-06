#!/usr/bin/env python3
"""
암호화폐 시장 데이터 테스트 스크립트
Gate.io API 연결 및 기본 기능을 테스트합니다.
"""

import asyncio
import sys
import os
# 상위 디렉터리(프로젝트 루트)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from crypto_monitor import CryptoMonitor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_connection():
    """API 연결을 테스트합니다."""
    print("=== Gate.io API 연결 테스트 ===")
    
    monitor = CryptoMonitor()
    
    try:
        # 거래량 상위 종목 테스트
        print("\n1. 거래량 상위 10개 종목 조회...")
        top_pairs = await monitor.get_top_volume_pairs(10)
        
        if top_pairs:
            print("✅ API 연결 성공!")
            print(f"거래량 상위 종목 {len(top_pairs)}개 조회 완료")
            
            print("\n📊 거래량 상위 5개 종목:")
            for i, ticker in enumerate(top_pairs[:5], 1):
                symbol = ticker.contract
                price = float(ticker.last)
                change_24h = float(ticker.change_percentage)
                volume_24h = float(ticker.volume_24h_quote)
                
                print(f"{i}. {symbol}")
                print(f"   가격: ${price:,.4f}")
                print(f"   24h 변동: {change_24h:+.2f}%")
                print(f"   거래량: ${volume_24h:,.0f}")
                print()
        else:
            print("❌ API 연결 실패 또는 데이터 없음")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    print("\n=== 테스트 완료 ===")


async def test_telegram_bot():
    """텔레그램 봇을 테스트합니다."""
    print("=== Telegram Bot 테스트 ===")
    
    monitor = CryptoMonitor()
    
    if not monitor.bot or not monitor.chat_id:
        print("❌ 텔레그램 설정이 없습니다.")
        print("config.py 파일에서 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정하세요.")
        return
    
    try:
        test_message = "🤖 암호화폐 모니터링 봇 테스트 메시지입니다."
        success = await monitor.send_telegram_message(test_message)
        
        if success:
            print("✅ 텔레그램 메시지 발송 성공!")
        else:
            print("❌ 텔레그램 메시지 발송 실패")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    print("\n=== 테스트 완료 ===")


async def test_conditions():
    """조건 확인을 테스트합니다."""
    print("=== 조건 확인 테스트 ===")
    
    monitor = CryptoMonitor()
    
    try:
        # BTC 티커 정보 가져오기
        tickers = monitor.spot_api.list_tickers(currency_pair="BTC_USDT")
        
        if tickers:
            btc_ticker = tickers[0]
            print(f"\n📊 BTC_USDT 현재 정보:")
            print(monitor.format_ticker_info(btc_ticker))
            
            # 조건 확인
            alerts = monitor.check_conditions(btc_ticker, "BTC_USDT")
            
            if alerts:
                print(f"\n🚨 조건 충족 알림 {len(alerts)}개:")
                for alert in alerts:
                    print(f"  • {alert}")
            else:
                print("\n✅ 현재 설정된 조건에 맞지 않습니다.")
                
        else:
            print("❌ BTC_USDT 정보를 가져올 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    print("\n=== 테스트 완료 ===")


async def main():
    """메인 테스트 함수"""
    print("🚀 암호화폐 모니터링 시스템 테스트를 시작합니다...\n")
    
    # 1. API 연결 테스트
    await test_api_connection()
    
    print("\n" + "="*50 + "\n")
    
    # 2. 조건 확인 테스트
    await test_conditions()
    
    print("\n" + "="*50 + "\n")
    
    # 3. 텔레그램 봇 테스트
    await test_telegram_bot()
    
    print(f"\n🎉 모든 테스트가 완료되었습니다!")
    print("\n다음 단계:")
    print("1. config.py에서 API 키와 텔레그램 설정을 확인하세요")
    print("2. watchlist.py에서 관심종목을 추가하세요") 
    print("3. 'python crypto_monitor.py once'로 한 번 실행해보세요")
    print("4. 'python crypto_monitor.py'로 지속적 모니터링을 시작하세요")


if __name__ == "__main__":
    asyncio.run(main())
