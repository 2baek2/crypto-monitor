#!/usr/bin/env python3
"""
다이버전스 알림 테스트 스크립트
"""
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from crypto_monitor import CryptoMonitor
from watchlist import WATCHLIST

async def test_divergence_alert():
    monitor = CryptoMonitor()
    # 관심 종목 중 첫 번째 심볼 선택 (원하는 심볼로 변경 가능)
    symbol = list(WATCHLIST.keys())[0]
    print(f"테스트 심볼: {symbol}")

    # 티커 정보 가져오기 (퓨처스/스팟 자동 선택)
    ticker = None
    if monitor.market_type == 'futures':
        tickers = await monitor._get_top_futures_volume(1)
        for t in tickers:
            if getattr(t, 'contract', getattr(t, 'currency_pair', 'Unknown')) == symbol:
                ticker = t
                break
    else:
        tickers = await monitor._get_top_spot_volume(1)
        for t in tickers:
            if t.currency_pair == symbol:
                ticker = t
                break

    if not ticker:
        print("❌ 티커 정보를 가져올 수 없습니다.")
        return

    # 다이버전스 조건 체크
    alerts = monitor.check_conditions(ticker, symbol)
    print(f"다이버전스 알림 결과: {alerts if alerts else '❌ 알림 없음'}")

    # 실제로 알림 메시지 전송 테스트 (텔레그램 설정 필요)
    # if alerts and monitor.bot and monitor.chat_id:
    #     print("📱 알림 메시지 전송 테스트...")
    #     for msg in alerts:
    #         await monitor.send_telegram_message(msg)
    #     print("✅ 메시지 전송 완료")
    # else:
    #     print("❌ 알림 메시지 없음 또는 텔레그램 설정 없음")

if __name__ == "__main__":
    asyncio.run(test_divergence_alert())