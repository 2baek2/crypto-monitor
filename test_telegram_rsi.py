#!/usr/bin/env python3
"""
텔레그램 RSI 알림 테스트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_monitor import CryptoMonitor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_telegram_rsi_alert():
    """텔레그램 RSI 알림을 테스트합니다."""
    print("=== 텔레그램 RSI 알림 테스트 ===")
    
    monitor = CryptoMonitor()
    
    if not monitor.bot or not monitor.chat_id:
        print("❌ 텔레그램 설정이 없습니다.")
        print("config.py에서 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정하세요.")
        return
    
    # 실제 RSI 조건을 만족하는 종목 찾기
    extreme_rsi_symbols = ["ASP_USDT", "ILV_USDT", "ZORA_USDT"]
    
    alerts_sent = 0
    
    for symbol in extreme_rsi_symbols:
        print(f"\n📊 {symbol} 분석 중...")
        
        try:
            # 티커 정보 가져오기
            tickers = monitor.spot_api.list_tickers(currency_pair=symbol)
            
            if not tickers:
                print(f"  ❌ {symbol} 티커 정보를 가져올 수 없습니다.")
                continue
            
            ticker = tickers[0]
            
            # 모든 조건 확인 (RSI 포함)
            alerts = monitor.check_conditions(ticker, symbol)
            
            if alerts:
                print(f"  🚨 알림 조건 충족! ({len(alerts)}개)")
                
                # 알림 메시지 생성
                message = f"🚨 <b>RSI 알림: {symbol}</b>\n\n"
                message += monitor.format_ticker_info(ticker) + "\n\n"
                message += "<b>조건 충족:</b>\n"
                for alert in alerts:
                    message += f"• {alert}\n"
                message += f"\n⏰ 시간: {asyncio.get_event_loop().time()}"
                
                print(f"  📱 텔레그램 메시지 발송...")
                success = await monitor.send_telegram_message(message)
                
                if success:
                    print(f"  ✅ 메시지 발송 성공!")
                    alerts_sent += 1
                else:
                    print(f"  ❌ 메시지 발송 실패")
                    
                # 메시지 간격 조절
                await asyncio.sleep(2)
            else:
                print(f"  ✅ 현재 조건에 맞지 않음")
                
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")
    
    print(f"\n📱 총 {alerts_sent}개의 RSI 알림을 발송했습니다.")


async def send_test_rsi_summary():
    """RSI 요약 정보를 텔레그램으로 발송합니다."""
    print("\n=== RSI 요약 정보 발송 ===")
    
    monitor = CryptoMonitor()
    
    if not monitor.bot:
        print("❌ 텔레그램 설정이 없습니다.")
        return
    
    # 상위 거래량 종목들의 RSI 요약
    message = "📊 <b>RSI 모니터링 요약</b>\n\n"
    message += f"🕒 시간: {asyncio.get_event_loop().time()}\n"
    message += "📈 조건: RSI ≤ 30 (과매도) 또는 RSI ≥ 70 (과매수)\n\n"
    
    try:
        top_pairs = await monitor.get_top_volume_pairs(5)
        
        for i, ticker in enumerate(top_pairs, 1):
            symbol = ticker.currency_pair
            current_price = float(ticker.last)
            change_24h = float(ticker.change_percentage)
            
            message += f"{i}. <b>{symbol}</b>\n"
            message += f"💰 ${current_price:,.6f} ({change_24h:+.2f}%)\n"
            
            # RSI 정보 가져오기
            try:
                rsi_summary = monitor.technical_analyzer.get_rsi_summary(
                    symbol, ['5m', '15m'], [7, 14, 21]
                )
                
                for timeframe, data in rsi_summary['timeframes'].items():
                    rsi_values = data['rsi_values']
                    rsi_text = []
                    for period in [7, 14, 21]:
                        rsi_key = f'rsi_{period}'
                        if rsi_key in rsi_values:
                            rsi_val = rsi_values[rsi_key]
                            emoji = "🔴" if rsi_val <= 30 else "🟢" if rsi_val >= 70 else "⚪"
                            rsi_text.append(f"RSI({period}): {rsi_val} {emoji}")
                    
                    if rsi_text:
                        message += f"📊 {timeframe}: {', '.join(rsi_text)}\n"
                        
            except Exception as e:
                message += f"📊 RSI 데이터 오류\n"
                logger.error(f"{symbol} RSI 요약 오류: {e}")
            
            message += "\n"
        
        message += "🤖 암호화폐 RSI 모니터링 봇"
        
        # 메시지 발송
        success = await monitor.send_telegram_message(message)
        
        if success:
            print("✅ RSI 요약 메시지 발송 성공!")
        else:
            print("❌ RSI 요약 메시지 발송 실패")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def main():
    """메인 함수"""
    print("📱 텔레그램 RSI 알림 테스트를 시작합니다...\n")
    
    # 1. RSI 알림 테스트
    await test_telegram_rsi_alert()
    
    print("\n" + "="*50)
    
    # 2. RSI 요약 정보 발송
    await send_test_rsi_summary()
    
    print(f"\n🎉 텔레그램 RSI 알림 테스트가 완료되었습니다!")


if __name__ == "__main__":
    asyncio.run(main())
