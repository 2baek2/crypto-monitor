import gate_api
from gate_api.exceptions import ApiException, GateApiException
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
import json

from config import (
    GATE_API_KEY, GATE_API_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    MONITOR_CONDITIONS, CHECK_INTERVAL_MINUTES
)
from watchlist import WATCHLIST
from technical_analysis import TechnicalAnalyzer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CryptoMonitor:
    def __init__(self):
        # Gate.io API 설정
        self.configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4"
        )
        # 대부분의 공개 API는 인증 없이 사용 가능
        if GATE_API_KEY and GATE_API_SECRET and GATE_API_KEY != "your_gate_api_key_here":
            # API 키 설정이 되어 있는 경우에만 인증 설정
            self.configuration.key = GATE_API_KEY
            self.configuration.secret = GATE_API_SECRET
        
        self.api_client = gate_api.ApiClient(self.configuration)
        self.spot_api = gate_api.SpotApi(self.api_client)
        
        # 기술적 분석기 초기화
        self.technical_analyzer = TechnicalAnalyzer(self.spot_api)
        
        # Telegram Bot 설정
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        self.chat_id = TELEGRAM_CHAT_ID
        
        # 이전 데이터 저장용
        self.previous_data = {}

    async def get_top_volume_pairs(self, limit: int = 30) -> List[Dict]:
        """당일 거래량 상위 종목을 가져옵니다."""
        try:
            # 모든 스팟 티커 정보 가져오기
            tickers = self.spot_api.list_tickers()
            
            # USDT 페어만 필터링하고 거래량으로 정렬
            usdt_tickers = [
                ticker for ticker in tickers 
                if ticker.currency_pair.endswith('_USDT') and float(ticker.quote_volume) > 0
            ]
            
            # 24시간 거래량 기준으로 정렬
            sorted_tickers = sorted(
                usdt_tickers, 
                key=lambda x: float(x.quote_volume), 
                reverse=True
            )
            
            return sorted_tickers[:limit]
            
        except (ApiException, GateApiException) as e:
            logger.error(f"Gate.io API 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"거래량 상위 종목 조회 오류: {e}")
            return []

    def check_conditions(self, ticker: Any, symbol: str) -> List[str]:
        """조건을 확인하고 알림 메시지를 반환합니다."""
        alerts = []
        
        try:
            # 현재 가격 정보
            current_price = float(ticker.last)
            price_change_24h = float(ticker.change_percentage)
            volume_24h = float(ticker.quote_volume)
            high_24h = float(ticker.high_24h)
            low_24h = float(ticker.low_24h)
            
            # 이전 데이터와 비교
            if symbol in self.previous_data:
                prev_volume = self.previous_data[symbol].get('volume', volume_24h)
                volume_change = volume_24h / prev_volume if prev_volume > 0 else 1
            else:
                volume_change = 1
            
            # 조건 확인
            conditions = MONITOR_CONDITIONS
            
            # 가격 변동률 조건 확인
            if 'price_change_24h_percent' in conditions:
                condition = conditions['price_change_24h_percent']
                if 'min' in condition and price_change_24h <= condition['min']:
                    alerts.append(f"📉 24시간 가격 변동률: {price_change_24h:.2f}% (임계값: {condition['min']}% 이하)")
                if 'max' in condition and price_change_24h >= condition['max']:
                    alerts.append(f"📈 24시간 가격 변동률: {price_change_24h:.2f}% (임계값: {condition['max']}% 이상)")
            
            # 거래량 변화 조건 확인
            if 'volume_change_24h' in conditions:
                condition = conditions['volume_change_24h']
                if 'min' in condition and volume_change >= condition['min']:
                    alerts.append(f"📊 거래량 증가: {volume_change:.2f}배 (임계값: {condition['min']}배 이상)")
            
            # RSI 조건 확인
            if 'rsi_conditions' in conditions and conditions['rsi_conditions'].get('enabled', False):
                rsi_config = conditions['rsi_conditions']
                timeframes = rsi_config.get('timeframes', ['5m', '15m'])
                periods = rsi_config.get('periods', [7, 14, 21])
                oversold = rsi_config.get('oversold', 30)
                overbought = rsi_config.get('overbought', 70)
                
                rsi_alerts = self.technical_analyzer.analyze_rsi_conditions(
                    symbol, timeframes, periods, oversold, overbought
                )
                alerts.extend(rsi_alerts)
            
            # 현재 데이터 저장
            self.previous_data[symbol] = {
                'price': current_price,
                'volume': volume_24h,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{symbol} 조건 확인 오류: {e}")
            
        return alerts

    async def send_telegram_message(self, message: str) -> bool:
        """텔레그램으로 메시지를 보냅니다."""
        if not self.bot or not self.chat_id:
            logger.warning("텔레그램 설정이 없어 메시지를 보낼 수 없습니다.")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except TelegramError as e:
            logger.error(f"텔레그램 메시지 발송 오류: {e}")
            return False

    def format_ticker_info(self, ticker: Any) -> str:
        """티커 정보를 포맷팅합니다."""
        try:
            symbol = ticker.currency_pair
            price = float(ticker.last)
            change_24h = float(ticker.change_percentage)
            volume_24h = float(ticker.quote_volume)
            high_24h = float(ticker.high_24h)
            low_24h = float(ticker.low_24h)
            
            # 종목명 가져오기
            coin_info = WATCHLIST.get(symbol, {})
            coin_name = coin_info.get('name', symbol.replace('_USDT', ''))
            
            info = f"""
<b>{coin_name} ({symbol})</b>
💰 현재가: ${price:,.4f}
📊 24h 변동률: {change_24h:+.2f}%
📈 24h 최고: ${high_24h:,.4f}
📉 24h 최저: ${low_24h:,.4f}
💹 24h 거래량: ${volume_24h:,.0f}
"""
            return info.strip()
        except Exception as e:
            logger.error(f"티커 정보 포맷팅 오류: {e}")
            return f"정보 표시 오류: {symbol}"

    async def monitor_markets(self):
        """시장을 모니터링합니다."""
        logger.info("암호화폐 모니터링을 시작합니다...")
        
        try:
            # 1. 거래량 상위 30개 종목 가져오기
            top_volume_pairs = await self.get_top_volume_pairs(30)
            
            if not top_volume_pairs:
                logger.warning("거래량 상위 종목을 가져올 수 없습니다.")
                return
            
            # 2. 관심 종목과 거래량 상위 종목을 합쳐서 모니터링
            all_symbols_to_check = set()
            
            # 관심 종목 추가
            for symbol in WATCHLIST.keys():
                all_symbols_to_check.add(symbol)
            
            # 거래량 상위 종목 추가
            for ticker in top_volume_pairs:
                all_symbols_to_check.add(ticker.currency_pair)
            
            logger.info(f"모니터링 대상 종목 수: {len(all_symbols_to_check)}")
            
            # 3. 각 종목별 조건 확인
            alert_messages = []
            
            for symbol in all_symbols_to_check:
                # 해당 심볼의 티커 정보 찾기
                ticker = None
                for t in top_volume_pairs:
                    if t.currency_pair == symbol:
                        ticker = t
                        break
                
                # 거래량 상위에 없는 관심종목의 경우 개별 조회
                if not ticker and symbol in WATCHLIST:
                    try:
                        ticker = self.spot_api.list_tickers(currency_pair=symbol)[0]
                    except Exception as e:
                        logger.warning(f"{symbol} 티커 정보를 가져올 수 없습니다: {e}")
                        continue
                
                if ticker:
                    alerts = self.check_conditions(ticker, symbol)
                    
                    if alerts:
                        message = f"🚨 <b>알림: {symbol}</b>\n"
                        message += self.format_ticker_info(ticker) + "\n\n"
                        message += "<b>조건 충족:</b>\n"
                        for alert in alerts:
                            message += f"• {alert}\n"
                        message += f"\n⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        alert_messages.append(message)
            
            # 4. 알림 메시지 발송
            if alert_messages:
                for message in alert_messages[:5]:  # 최대 5개까지만 발송
                    await self.send_telegram_message(message)
                    await asyncio.sleep(1)  # 메시지 간격 조절
                
                logger.info(f"{len(alert_messages)}개의 알림을 발송했습니다.")
            else:
                logger.info("조건에 맞는 종목이 없습니다.")
            
            # 5. 거래량 상위 종목 정보 (선택적 발송)
            if datetime.now().hour == 9 and datetime.now().minute < CHECK_INTERVAL_MINUTES:
                top_5_message = "📊 <b>오늘의 거래량 상위 5개 종목</b>\n\n"
                for i, ticker in enumerate(top_volume_pairs[:5], 1):
                    symbol = ticker.currency_pair
                    price = float(ticker.last)
                    change_24h = float(ticker.change_percentage)
                    volume_24h = float(ticker.quote_volume)
                    
                    top_5_message += f"{i}. <b>{symbol}</b>\n"
                    top_5_message += f"   💰 ${price:,.4f} ({change_24h:+.2f}%)\n"
                    top_5_message += f"   📊 거래량: ${volume_24h:,.0f}\n\n"
                
                await self.send_telegram_message(top_5_message)
                
        except Exception as e:
            logger.error(f"시장 모니터링 오류: {e}")
            error_message = f"🔴 모니터링 오류 발생: {str(e)}\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await self.send_telegram_message(error_message)

    async def run_continuous_monitoring(self):
        """지속적인 모니터링을 실행합니다."""
        logger.info(f"지속적 모니터링 시작 (체크 간격: {CHECK_INTERVAL_MINUTES}분)")
        
        while True:
            try:
                await self.monitor_markets()
                
                # 다음 체크까지 대기
                await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                logger.info("사용자에 의해 모니터링이 중단되었습니다.")
                break
            except Exception as e:
                logger.error(f"지속적 모니터링 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 후 재시도

    def run_once(self):
        """한 번만 모니터링을 실행합니다."""
        logger.info("단일 모니터링 실행...")
        asyncio.run(self.monitor_markets())

    def run_continuous(self):
        """지속적 모니터링을 시작합니다."""
        asyncio.run(self.run_continuous_monitoring())


if __name__ == "__main__":
    import sys
    
    monitor = CryptoMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # 한 번만 실행
        monitor.run_once()
    else:
        # 지속적 실행
        monitor.run_continuous()
