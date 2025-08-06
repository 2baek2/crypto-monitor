import gate_api
from gate_api.exceptions import ApiException, GateApiException
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Any
import json
import pytz

from config import (
    GATE_API_KEY, GATE_API_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    MONITOR_CONDITIONS, CHECK_INTERVAL_MINUTES, MARKET_SETTINGS, ALERT_COOLDOWN,
    NOTIFICATION_SCHEDULE
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
        self.futures_api = gate_api.FuturesApi(self.api_client)
        
        # 시장 설정
        self.market_settings = MARKET_SETTINGS
        self.market_type = MARKET_SETTINGS.get('market_type', 'spot')
        self.settle = MARKET_SETTINGS.get('settle', 'usdt')
        self.top_volume_limit = MARKET_SETTINGS.get('top_volume_limit', 30)
        self.max_alerts_per_cycle = MARKET_SETTINGS.get('max_alerts_per_cycle', 5)
        
        # 모니터링 조건
        self.monitor_conditions = MONITOR_CONDITIONS
        
        # 기술적 분석기 초기화
        self.technical_analyzer = TechnicalAnalyzer(
            spot_api=self.spot_api,
            futures_api=self.futures_api,
            market_type=self.market_type
        )        # Telegram Bot 설정
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        self.chat_id = TELEGRAM_CHAT_ID
        
        # 이전 데이터 저장용
        self.previous_data = {}
        
        # 전체 알림 캐시 (중복 방지용)
        self.alert_cache = {}  # {cache_key: last_alert_time}

    def timeframe_to_minutes(self, timeframe: str) -> int:
        """타임프레임을 분 단위로 변환합니다."""
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24 * 60
        else:
            # 기본값 (알 수 없는 형식)
            return 5
    
    def get_smallest_timeframe_minutes(self) -> int:
        """설정된 timeframe 중 가장 작은 것을 분 단위로 반환합니다."""
        all_timeframes = []
        
        # RSI 조건의 timeframes
        if 'rsi_conditions' in MONITOR_CONDITIONS and MONITOR_CONDITIONS['rsi_conditions'].get('enabled'):
            all_timeframes.extend(MONITOR_CONDITIONS['rsi_conditions'].get('timeframes', []))
        
        # 다이버전스 조건의 timeframes
        if 'divergence_conditions' in MONITOR_CONDITIONS and MONITOR_CONDITIONS['divergence_conditions'].get('enabled'):
            all_timeframes.extend(MONITOR_CONDITIONS['divergence_conditions'].get('timeframes', []))
        
        if not all_timeframes:
            return CHECK_INTERVAL_MINUTES  # 기본값
        
        # 가장 작은 timeframe 찾기
        min_minutes = min(self.timeframe_to_minutes(tf) for tf in all_timeframes)
        return min_minutes
    
    def get_next_candle_close_time(self, timeframe_minutes: int) -> datetime:
        """다음 봉 마감 시간을 계산합니다."""
        now = datetime.now()
        
        # 현재 시간을 timeframe 단위로 올림
        minutes_since_midnight = now.hour * 60 + now.minute
        current_candle_start = (minutes_since_midnight // timeframe_minutes) * timeframe_minutes
        next_candle_start = current_candle_start + timeframe_minutes
        
        # 다음 봉 시작 시간 (= 현재 봉 마감 시간)
        next_candle_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=next_candle_start)
        
        # 만약 계산된 시간이 과거라면 다음 날로 이동
        if next_candle_time <= now:
            next_candle_time += timedelta(days=1)
        
        return next_candle_time

    def generate_alert_cache_key(self, symbol: str, condition_type: str, additional_info: str = "") -> str:
        """알림 캐시 키를 생성합니다."""
        if ALERT_COOLDOWN.get('per_condition_type', True):
            # 조건 타입별 개별 쿨다운
            if additional_info:
                return f"{symbol}_{condition_type}_{additional_info}"
            else:
                return f"{symbol}_{condition_type}"
        else:
            # 심볼 전체 쿨다운
            return symbol
    
    def is_alert_in_cooldown(self, cache_key: str) -> bool:
        """알림이 쿨다운 중인지 확인합니다."""
        if not ALERT_COOLDOWN.get('enabled', False):
            return False
            
        if cache_key not in self.alert_cache:
            return False
            
        last_alert_time = self.alert_cache[cache_key]
        current_time = datetime.now()
        time_diff_minutes = (current_time - last_alert_time).total_seconds() / 60
        cooldown_minutes = ALERT_COOLDOWN.get('cooldown_minutes', 30)
        
        if time_diff_minutes < cooldown_minutes:
            logger.debug(f"알림 쿨다운 중: {cache_key} ({time_diff_minutes:.1f}분 경과/{cooldown_minutes}분 필요)")
            return True
            
        return False
    
    def update_alert_cache(self, cache_key: str):
        """알림 캐시를 업데이트합니다."""
        if ALERT_COOLDOWN.get('enabled', False):
            self.alert_cache[cache_key] = datetime.now()

    async def get_top_volume_pairs(self, limit: int = None) -> List[Dict]:
        """거래 대금 상위 종목을 가져옵니다."""
        if limit is None:
            limit = self.top_volume_limit
            
        try:
            if self.market_type == 'futures':
                return await self._get_top_futures_volume(limit)
            else:
                return await self._get_top_spot_volume(limit)
                
        except Exception as e:
            logger.error(f"거래 대금 상위 종목 조회 오류: {e}")
            return []

    async def _get_top_spot_volume(self, limit: int) -> List[Dict]:
        """스팟 시장의 거래 대금 상위 종목을 가져옵니다."""
        try:
            # 모든 스팟 티커 정보 가져오기
            tickers = self.spot_api.list_tickers()
            
            # USDT 페어만 필터링하고 거래 대금으로 정렬
            usdt_tickers = [
                ticker for ticker in tickers 
                if ticker.currency_pair.endswith('_USDT') and float(ticker.quote_volume) > 0
            ]
            
            # 24시간 거래 대금 기준으로 정렬 (USDT)
            sorted_tickers = sorted(
                usdt_tickers, 
                key=lambda x: float(x.quote_volume), 
                reverse=True
            )
            
            return sorted_tickers[:limit]
            
        except (ApiException, GateApiException) as e:
            logger.error(f"Gate.io Spot API 오류: {e}")
            return []

    async def _get_top_futures_volume(self, limit: int) -> List[Dict]:
        """퓨처스 시장의 거래 대금 상위 종목을 가져옵니다."""
        try:
            # 퓨처스 티커 정보 가져오기
            tickers = self.futures_api.list_futures_tickers(settle=self.settle)
            
            # 거래 대금이 있는 계약만 필터링
            active_tickers = [
                ticker for ticker in tickers 
                if float(getattr(ticker, 'volume_24h_settle', 0)) > 0
            ]
            
            # 24시간 거래 대금 기준으로 정렬 (USDT 기준)
            sorted_tickers = sorted(
                active_tickers,
                key=lambda x: float(x.volume_24h_settle),
                reverse=True
            )
            
            return sorted_tickers[:limit]
            
        except (ApiException, GateApiException) as e:
            logger.error(f"Gate.io Futures API 오류: {e}")
            return []

    def check_conditions(self, ticker: Any, symbol: str) -> List[str]:
        """조건을 확인하고 알림 메시지를 반환합니다."""
        alerts = []
        
        try:
            # 현재 가격 정보 (시장 타입에 따라 다른 속성 사용)
            current_price = float(ticker.last)
            price_change_24h = float(ticker.change_percentage)
            high_24h = float(ticker.high_24h)
            low_24h = float(ticker.low_24h)
            
            # 거래량 정보 - 시장 타입에 따라 다른 속성 사용
            if self.market_type == 'futures':
                # Futures는 volume_24h_settle 또는 volume_24h 사용
                if hasattr(ticker, 'volume_24h_settle'):
                    volume_24h = float(ticker.volume_24h_settle)
                elif hasattr(ticker, 'volume_24h'):
                    volume_24h = float(ticker.volume_24h)
                else:
                    volume_24h = 0
            else:
                # Spot은 quote_volume 사용
                volume_24h = float(getattr(ticker, 'quote_volume', 0))
            
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
                    cache_key = self.generate_alert_cache_key(symbol, "price_drop", f"{condition['min']}")
                    if not self.is_alert_in_cooldown(cache_key):
                        alert_msg = f"📉 24시간 가격 변동률: {price_change_24h:.2f}% (임계값: {condition['min']}% 이하)"
                        alerts.append(alert_msg)
                        self.update_alert_cache(cache_key)
                        
                if 'max' in condition and price_change_24h >= condition['max']:
                    cache_key = self.generate_alert_cache_key(symbol, "price_rise", f"{condition['max']}")
                    if not self.is_alert_in_cooldown(cache_key):
                        alert_msg = f"📈 24시간 가격 변동률: {price_change_24h:.2f}% (임계값: {condition['max']}% 이상)"
                        alerts.append(alert_msg)
                        self.update_alert_cache(cache_key)
            
            # 거래량 변화 조건 확인
            if 'volume_change_24h' in conditions:
                condition = conditions['volume_change_24h']
                if 'min' in condition and volume_change >= condition['min']:
                    cache_key = self.generate_alert_cache_key(symbol, "volume_surge", f"{condition['min']}")
                    if not self.is_alert_in_cooldown(cache_key):
                        alert_msg = f"📊 거래량 증가: {volume_change:.2f}배 (임계값: {condition['min']}배 이상)"
                        alerts.append(alert_msg)
                        self.update_alert_cache(cache_key)
            
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
                
                # RSI 알림에 쿨다운 적용
                for rsi_alert in rsi_alerts:
                    # RSI 알림 타입 파악 (과매도/과매수/시간프레임 정보 포함)
                    alert_type = "rsi_oversold" if "과매도" in rsi_alert else "rsi_overbought"
                    timeframe_info = ""
                    for tf in timeframes:
                        if tf in rsi_alert:
                            timeframe_info = tf
                            break
                    
                    cache_key = self.generate_alert_cache_key(symbol, alert_type, timeframe_info)
                    if not self.is_alert_in_cooldown(cache_key):
                        alerts.append(rsi_alert)
                        self.update_alert_cache(cache_key)
            
            # RSI 다이버전스 조건 확인
            if 'divergence_conditions' in conditions and conditions['divergence_conditions'].get('enabled', False):
                div_config = conditions['divergence_conditions']
                div_timeframes = div_config.get('timeframes', ['5m', '15m'])
                rsi_period = div_config.get('rsi_period', 14)
                lookback_range = tuple(div_config.get('lookback_range', [5, 60]))
                include_hidden = div_config.get('include_hidden', False)
                recent_bars_only = div_config.get('recent_bars_only', 5)
                
                for timeframe in div_timeframes:
                    try:
                        divergence_alerts = self.technical_analyzer.detect_rsi_divergence(
                            symbol, timeframe, rsi_period, lookback_range, recent_bars_only
                        )
                        
                        # Hidden 다이버전스 필터링
                        if not include_hidden:
                            divergence_alerts = [
                                alert for alert in divergence_alerts 
                                if "Hidden" not in alert
                            ]
                        
                        # 다이버전스 알림에 쿨다운 적용
                        for divergence_msg in divergence_alerts:
                            # 다이버전스 타입 추출
                            div_type = "unknown"
                            if "Regular Bullish" in divergence_msg:
                                div_type = "regular_bullish"
                            elif "Regular Bearish" in divergence_msg:
                                div_type = "regular_bearish"
                            elif "Hidden Bullish" in divergence_msg:
                                div_type = "hidden_bullish"
                            elif "Hidden Bearish" in divergence_msg:
                                div_type = "hidden_bearish"
                            
                            cache_key = self.generate_alert_cache_key(symbol, "divergence", f"{timeframe}_{div_type}")
                            if not self.is_alert_in_cooldown(cache_key):
                                alerts.append(divergence_msg)
                                self.update_alert_cache(cache_key)
                                
                        if divergence_alerts:
                            logger.info(f"다이버전스 신호 발견: {symbol} {timeframe} - {len(divergence_alerts)}개")
                            
                    except Exception as e:
                        logger.error(f"{symbol} {timeframe} 다이버전스 분석 오류: {e}")
                        continue
            
            # 현재 데이터 저장
            self.previous_data[symbol] = {
                'price': current_price,
                'volume': volume_24h,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{symbol} 조건 확인 오류: {e}")
            
        return alerts

    def is_notification_allowed(self) -> bool:
        """현재 시간에 알림이 허용되는지 확인합니다."""
        try:
            # NOTIFICATION_SCHEDULE 설정이 없거나 비활성화된 경우 항상 허용
            if not hasattr(self, 'notification_schedule') or not NOTIFICATION_SCHEDULE.get('enabled', False):
                return True
            
            # 한국시간으로 현재 시간 가져오기
            timezone = pytz.timezone(NOTIFICATION_SCHEDULE.get('timezone', 'Asia/Seoul'))
            now = datetime.now(timezone)
            current_hour = now.hour
            current_weekday = now.weekday()  # 0=월요일, 6=일요일
            is_weekend = current_weekday >= 5  # 토요일(5), 일요일(6)
            
            # 주말 알림 비활성화 설정 확인
            if is_weekend and NOTIFICATION_SCHEDULE.get('disable_weekends', False):
                logger.info(f"주말 알림 비활성화: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                return False
            
            # 조용한 시간 설정
            quiet_hours = NOTIFICATION_SCHEDULE.get('quiet_hours', {})
            
            # 주말 전용 조용한 시간 설정이 있고 활성화된 경우
            if is_weekend:
                weekend_quiet = NOTIFICATION_SCHEDULE.get('weekend_quiet_hours', {})
                if weekend_quiet.get('enabled', False):
                    quiet_hours = weekend_quiet
            
            # 시간 파싱 (HH:MM 형식에서 시간만 추출)
            start_time_str = quiet_hours.get('start', '22:00')
            end_time_str = quiet_hours.get('end', '08:00')
            start_hour = int(start_time_str.split(':')[0])
            end_hour = int(end_time_str.split(':')[0])
            
            # 시간 비교 (start_hour가 end_hour보다 큰 경우 다음날까지 처리)
            if start_hour <= end_hour:
                # 같은 날 내 시간대 (예: 08시 ~ 22시 허용)
                is_quiet = start_hour <= current_hour <= end_hour
                is_allowed = not is_quiet
            else:
                # 다음날로 넘어가는 시간대 (예: 22시 ~ 08시 조용)
                is_quiet = current_hour >= start_hour or current_hour < end_hour
                is_allowed = not is_quiet
            
            if not is_allowed:
                logger.info(f"조용한 시간 알림 차단: {now.strftime('%Y-%m-%d %H:%M:%S')} (설정: {start_time_str} ~ {end_time_str})")
            
            return is_allowed
            
        except Exception as e:
            logger.error(f"알림 시간 확인 오류: {e}")
            return True  # 오류 시 기본적으로 허용

    async def send_telegram_message(self, message: str) -> bool:
        """텔레그램으로 메시지를 보냅니다."""
        if not self.bot or not self.chat_id:
            logger.warning("텔레그램 설정이 없어 메시지를 보낼 수 없습니다.")
            return False
        
        # 알림 시간 제한 확인 - silent 모드 결정
        is_silent = not self.is_notification_allowed()
        if is_silent:
            logger.info("조용한 시간으로 인해 알림을 무음으로 발송합니다.")
            
        try:
            # HTML 특수문자 이스케이프 처리
            import html
            safe_message = html.escape(message)
            
            # HTML 태그를 다시 복원 (안전한 태그만)
            safe_message = safe_message.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
            safe_message = safe_message.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=safe_message,
                parse_mode='HTML',
                disable_notification=is_silent  # 조용한 시간에는 알림음 없이
            )
            return True
        except TelegramError as e:
            logger.error(f"텔레그램 HTML 메시지 발송 오류: {e}")
            # HTML 파싱 실패시 일반 텍스트로 재시도
            try:
                # HTML 태그 제거
                plain_message = message.replace('<b>', '').replace('</b>', '')
                plain_message = plain_message.replace('<i>', '').replace('</i>', '')
                
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=plain_message,
                    disable_notification=is_silent  # 조용한 시간에는 알림음 없이
                )
                return True
            except TelegramError as e2:
                logger.error(f"텔레그램 일반 텍스트 메시지 발송 오류: {e2}")
                return False

    def format_ticker_info(self, ticker: Any) -> str:
        """티커 정보를 포맷팅합니다."""
        try:
            if self.market_type == 'futures':
                return self._format_futures_ticker(ticker)
            else:
                return self._format_spot_ticker(ticker)
        except Exception as e:
            symbol = getattr(ticker, 'contract', getattr(ticker, 'currency_pair', 'Unknown'))
            logger.error(f"티커 정보 포맷팅 오류: {e}")
            return f"정보 표시 오류: {symbol}"

    def _format_spot_ticker(self, ticker: Any) -> str:
        """스팟 티커 정보를 포맷팅합니다."""
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

    def _format_futures_ticker(self, ticker: Any) -> str:
        """퓨처스 티커 정보를 포맷팅합니다."""
        symbol = getattr(ticker, 'contract', getattr(ticker, 'currency_pair', 'Unknown'))
        price = float(ticker.last)
        change_24h = float(ticker.change_percentage)
        volume_24h = float(getattr(ticker, 'volume_24h_usdt', getattr(ticker, 'volume_24h', 0)))
        high_24h = float(ticker.high_24h)
        low_24h = float(ticker.low_24h)
        
        # 퓨처스 계약명에서 기본 코인명 추출
        base_symbol = symbol.split('_')[0] if '_' in symbol else symbol
        coin_name = base_symbol
        
        info = f"""
<b>{coin_name} Futures ({symbol})</b>
💰 현재가: ${price:,.4f}
📊 24h 변동률: {change_24h:+.2f}%
📈 24h 최고: ${high_24h:,.4f}
📉 24h 최저: ${low_24h:,.4f}
💹 24h 거래량: ${volume_24h:,.0f}
"""
        return info.strip()

    async def monitor_markets(self):
        """시장을 모니터링합니다."""
        logger.info("암호화폐 모니터링을 시작합니다...")
        
        try:
            # 1. 거래 대금 상위 종목 가져오기
            top_volume_pairs = await self.get_top_volume_pairs(self.top_volume_limit)
            
            if not top_volume_pairs:
                logger.warning("거래 대금 상위 종목을 가져올 수 없습니다.")
                return
            
            # 2. 관심 종목과 거래 대금 상위 종목을 합쳐서 모니터링
            all_symbols_to_check = set()
            
            # 관심 종목 추가
            for symbol in WATCHLIST.keys():
                all_symbols_to_check.add(symbol)
            
            # 거래 대금 상위 종목 추가
            for ticker in top_volume_pairs:
                if self.market_type == 'futures':
                    all_symbols_to_check.add(getattr(ticker, 'contract', getattr(ticker, 'currency_pair', 'Unknown')))
                else:
                    all_symbols_to_check.add(ticker.currency_pair)
            
            logger.info(f"모니터링 대상 종목 수: {len(all_symbols_to_check)}")
            
            # 3. 각 종목별 조건 확인
            alert_messages = []
            
            for symbol in all_symbols_to_check:
                # 해당 심볼의 티커 정보 찾기
                ticker = None
                for t in top_volume_pairs:
                    ticker_symbol = t.contract if self.market_type == 'futures' else t.currency_pair
                    if ticker_symbol == symbol:
                        ticker = t
                        break
                
                # 거래 대금 상위에 없는 관심종목의 경우 개별 조회
                if not ticker and symbol in WATCHLIST:
                    try:
                        if self.market_type == 'futures':
                            # Futures의 경우 개별 조회 방법이 다를 수 있음
                            # 현재는 상위 거래량에서만 처리
                            continue
                        else:
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
            
            # 5. 거래 대금 상위 종목 정보 (선택적 발송)
            if datetime.now().hour == 9 and datetime.now().minute < CHECK_INTERVAL_MINUTES:
                market_name = "Futures" if self.market_type == 'futures' else "Spot"
                top_5_message = f"📊 <b>오늘의 {market_name} 거래 대금 상위 5개 종목</b>\n\n"
                for i, ticker in enumerate(top_volume_pairs[:5], 1):
                    if self.market_type == 'futures':
                        symbol = getattr(ticker, 'contract', getattr(ticker, 'currency_pair', 'Unknown'))
                        volume_24h = float(getattr(ticker, 'volume_24h_settle', ticker.volume_24h))
                    else:
                        symbol = ticker.currency_pair
                        volume_24h = float(ticker.quote_volume)
                        
                    price = float(ticker.last)
                    change_24h = float(ticker.change_percentage)
                    
                    top_5_message += f"{i}. <b>{symbol}</b>\n"
                    top_5_message += f"   💰 ${price:,.4f} ({change_24h:+.2f}%)\n"
                    top_5_message += f"   📊 거래 대금: ${volume_24h:,.0f}\n\n"
                
                await self.send_telegram_message(top_5_message)
                
        except Exception as e:
            logger.error(f"시장 모니터링 오류: {e}")
            error_message = f"🔴 모니터링 오류 발생: {str(e)}\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await self.send_telegram_message(error_message)

    async def run_continuous_monitoring(self):
        """지속적인 모니터링을 스마트 스케줄링으로 실행합니다."""
        smallest_tf_minutes = self.get_smallest_timeframe_minutes()
        
        logger.info(f"지속적 모니터링 시작")
        logger.info(f"  - 가장 작은 타임프레임: {smallest_tf_minutes}분")
        logger.info(f"  - 기본 체크 간격: {CHECK_INTERVAL_MINUTES}분")
        
        # 첫 번째 즉시 실행
        logger.info("🚀 시작 시 즉시 모니터링 실행...")
        try:
            await self.monitor_markets()
        except Exception as e:
            logger.error(f"초기 모니터링 오류: {e}")
        
        # 다음 봉 마감까지 대기 후 실행
        next_candle_time = self.get_next_candle_close_time(smallest_tf_minutes)
        wait_seconds = (next_candle_time - datetime.now()).total_seconds()
        
        if wait_seconds > 0:
            logger.info(f"⏰ 다음 {smallest_tf_minutes}분봉 마감까지 {wait_seconds:.0f}초 대기...")
            logger.info(f"   다음 실행 시간: {next_candle_time.strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(wait_seconds)
        
        # 봉 마감 시점에 한 번 실행
        logger.info(f"📊 {smallest_tf_minutes}분봉 마감 - 모니터링 실행...")
        try:
            await self.monitor_markets()
        except Exception as e:
            logger.error(f"봉 마감 시점 모니터링 오류: {e}")
        
        # 이후부터는 정기적인 간격으로 실행
        logger.info(f"🔄 정기 모니터링 시작 (간격: {CHECK_INTERVAL_MINUTES}분)")
        
        while True:
            try:
                # CHECK_INTERVAL_MINUTES 간격으로 대기
                await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
                
                logger.info(f"⏰ 정기 모니터링 실행 ({datetime.now().strftime('%H:%M:%S')})")
                await self.monitor_markets()
                
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
