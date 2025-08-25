import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import pytz

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """기술적 분석을 수행하는 클래스"""
    
    def __init__(self, client: Client, market_type='spot'):
        self.client = client
        self.market_type = market_type
        
    def get_candlestick_data(self, symbol: str, interval: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """캔들스틱 데이터를 가져와서 DataFrame으로 변환합니다."""
        try:
            # Binance 간격 매핑
            interval_mapping = {
                "1m": Client.KLINE_INTERVAL_1MINUTE,
                "5m": Client.KLINE_INTERVAL_5MINUTE, 
                "15m": Client.KLINE_INTERVAL_15MINUTE,
                "1h": Client.KLINE_INTERVAL_1HOUR,
                "4h": Client.KLINE_INTERVAL_4HOUR,
                "1d": Client.KLINE_INTERVAL_1DAY
            }
            
            binance_interval = interval_mapping.get(interval, Client.KLINE_INTERVAL_5MINUTE)
            
            # 시장 타입에 따라 다른 API 사용
            if self.market_type == 'futures':
                candlesticks = self.client.futures_klines(
                    symbol=symbol,
                    interval=binance_interval,
                    limit=limit
                )
            else:
                candlesticks = self.client.get_klines(
                    symbol=symbol,
                    interval=binance_interval,
                    limit=limit
                )
            
            if not candlesticks:
                logger.warning(f"{symbol} {interval} 캔들스틱 데이터가 없습니다.")
                return None
                
            # DataFrame으로 변환 (Binance 표준 형식)
            data = []
            for candle in candlesticks:
                data.append({
                    'timestamp': int(candle[0]) // 1000,  # milliseconds to seconds
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.debug(f"{symbol} {interval} 데이터 {len(df)}개 로드 완료")
            return df
            
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"{symbol} {interval} 캔들스틱 데이터 조회 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"{symbol} {interval} 데이터 처리 오류: {e}")
            return None
    
    def calculate_rsi(self, df: pd.DataFrame, periods: List[int]) -> Dict[str, float]:
        """여러 기간의 RSI를 계산합니다."""
        rsi_values = {}
        
        if df is None or len(df) < max(periods) + 10:
            logger.warning(f"RSI 계산을 위한 데이터가 부족합니다. (필요: {max(periods) + 10}개, 실제: {len(df) if df is not None else 0}개)")
            return rsi_values
        
        try:
            for period in periods:
                if len(df) >= period + 10:  # RSI 계산에 충분한 데이터가 있는지 확인
                    rsi_indicator = RSIIndicator(df['close'], window=period)
                    rsi_series = rsi_indicator.rsi()
                    
                    # 최신 RSI 값 (NaN이 아닌 마지막 값)
                    latest_rsi = None
                    for i in range(len(rsi_series) - 1, -1, -1):
                        if not pd.isna(rsi_series.iloc[i]):
                            latest_rsi = rsi_series.iloc[i]
                            break
                    
                    if latest_rsi is not None:
                        rsi_values[f'rsi_{period}'] = round(latest_rsi, 2)
                        logger.debug(f"RSI({period}): {latest_rsi:.2f}")
                else:
                    logger.warning(f"RSI({period}) 계산을 위한 데이터가 부족합니다.")
                    
        except Exception as e:
            logger.error(f"RSI 계산 오류: {e}")
            
        return rsi_values
    
    def analyze_rsi_conditions(self, symbol: str, timeframes: List[str], periods: List[int], 
                             oversold: float, overbought: float) -> List[str]:
        """RSI 조건을 분석하고 알림 메시지를 생성합니다."""
        alerts = []
        
        try:
            for timeframe in timeframes:
                # 캔들스틱 데이터 가져오기
                df = self.get_candlestick_data(symbol, timeframe, limit=max(periods) + 50)
                
                if df is None:
                    continue
                
                # RSI 계산
                rsi_values = self.calculate_rsi(df, periods)
                
                if not rsi_values:
                    continue
                
                # 현재가 정보
                current_price = df['close'].iloc[-1]
                
                # RSI 조건 확인
                timeframe_alerts = []
                oversold_signals = []
                overbought_signals = []
                
                for period in periods:
                    rsi_key = f'rsi_{period}'
                    if rsi_key in rsi_values:
                        rsi_value = rsi_values[rsi_key]
                        
                        if rsi_value <= oversold:
                            oversold_signals.append(f"RSI({period}): {rsi_value}")
                        elif rsi_value >= overbought:
                            overbought_signals.append(f"RSI({period}): {rsi_value}")
                
                # 알림 메시지 생성
                if oversold_signals:
                    alert_msg = f"📉 {timeframe} 과매도 신호: {', '.join(oversold_signals)}"
                    timeframe_alerts.append(alert_msg)
                    
                if overbought_signals:
                    alert_msg = f"📈 {timeframe} 과매수 신호: {', '.join(overbought_signals)}"
                    timeframe_alerts.append(alert_msg)
                
                # RSI 정보 표시 (조건에 맞지 않더라도 현재 값 표시)
                if rsi_values and not timeframe_alerts:
                    rsi_info = []
                    for period in sorted(periods):
                        rsi_key = f'rsi_{period}'
                        if rsi_key in rsi_values:
                            rsi_info.append(f"RSI({period}): {rsi_values[rsi_key]}")
                    
                    if rsi_info:
                        info_msg = f"📊 {timeframe} RSI: {', '.join(rsi_info)}"
                        # 디버그 정보로 로깅 (알림으로는 보내지 않음)
                        logger.debug(f"{symbol} - {info_msg}")
                
                alerts.extend(timeframe_alerts)
                
        except Exception as e:
            logger.error(f"{symbol} RSI 분석 오류: {e}")
            
        return alerts
    
    def get_rsi_summary(self, symbol: str, timeframes: List[str], periods: List[int]) -> Dict:
        """RSI 요약 정보를 반환합니다 (알림용)."""
        summary = {
            'symbol': symbol,
            'timeframes': {}
        }
        
        try:
            for timeframe in timeframes:
                df = self.get_candlestick_data(symbol, timeframe, limit=max(periods) + 50)
                
                if df is None:
                    continue
                    
                rsi_values = self.calculate_rsi(df, periods)
                
                if rsi_values:
                    summary['timeframes'][timeframe] = {
                        'current_price': round(df['close'].iloc[-1], 6),
                        'rsi_values': rsi_values,
                        'timestamp': df['datetime'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
        except Exception as e:
            logger.error(f"{symbol} RSI 요약 생성 오류: {e}")
            
        return summary

    def find_pivots(self, data: pd.Series, left_bars: int, right_bars: int) -> Tuple[List[int], List[int]]:
        """
        피벗 하이/로우를 찾습니다. (TradingView Pine Script의 ta.pivotlow/ta.pivothigh와 유사한 로직)
        - 피벗 로우: 특정 지점의 값이 왼쪽(lbL)과 오른쪽(lbR)의 모든 값보다 '작은' 지점.
        - 피벗 하이: 특정 지점의 값이 왼쪽(lbL)과 오른쪽(lbR)의 모든 값보다 '큰' 지점.
        """
        pivot_lows = []
        pivot_highs = []

        if len(data) < left_bars + right_bars + 1:
            return [], []

        for i in range(left_bars, len(data) - right_bars):
            pivot_val = data.iloc[i]
            
            # .iloc를 사용하여 슬라이싱
            left_window = data.iloc[i - left_bars : i]
            right_window = data.iloc[i + 1 : i + right_bars + 1]
            
            # 피벗 로우: pivot_val이 주변 모든 값보다 작아야 함
            if (left_window > pivot_val).all() and (right_window > pivot_val).all():
                pivot_lows.append(i)

            # 피벗 하이: pivot_val이 주변 모든 값보다 커야 함
            if (left_window < pivot_val).all() and (right_window < pivot_val).all():
                pivot_highs.append(i)
                
        return pivot_lows, pivot_highs

    def detect_immediate_rsi_divergence(self, symbol: str, timeframe: str = "5m", 
                                       rsi_period: int = 14, lookback_periods: int = 10) -> List[str]:
        """가장 최근 RSI와 가격을 비교하여 즉시 다이버전스를 감지합니다."""
        divergence_signals = []
        try:
            kst = pytz.timezone('Asia/Seoul')
            current_time = datetime.now(kst)
            
            # 데이터 로드
            df = self.get_candlestick_data(symbol, timeframe, limit=lookback_periods + rsi_period + 5)
            if df is None or len(df) < rsi_period + 5:
                logger.warning(f"{symbol} 데이터 부족으로 즉시 다이버전스 분석 중단")
                return []

            # RSI 계산
            df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()
            df = df.dropna().reset_index(drop=True)
            if len(df) < 10:
                return []

            # 현재와 이전 데이터
            current_close = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            prev_rsi = df['rsi'].iloc[-2]
            
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M')
            
            # 즉시 다이버전스 체크 (현재 vs 바로 이전)
            price_change_pct = ((current_close - prev_close) / prev_close) * 100
            rsi_change = current_rsi - prev_rsi
            
            # 의미있는 변화인지 확인 (가격 0.5% 이상, RSI 2포인트 이상)
            if abs(price_change_pct) >= 0.5 and abs(rsi_change) >= 2:
                # Bullish Divergence: 가격 하락, RSI 상승
                if price_change_pct < 0 and rsi_change > 0:
                    divergence_signals.append(
                        f"🟢 즉시 Bullish Divergence ({timeframe}) - {current_time_str}\n"
                        f"가격: {price_change_pct:.2f}% ↓, RSI: +{rsi_change:.1f} ↑"
                    )
                    logger.info(f"{symbol} 즉시 Bullish Divergence: 가격 {price_change_pct:.2f}% 하락, RSI +{rsi_change:.1f}")
                
                # Bearish Divergence: 가격 상승, RSI 하락
                elif price_change_pct > 0 and rsi_change < 0:
                    divergence_signals.append(
                        f"🔴 즉시 Bearish Divergence ({timeframe}) - {current_time_str}\n"
                        f"가격: +{price_change_pct:.2f}% ↑, RSI: {rsi_change:.1f} ↓"
                    )
                    logger.info(f"{symbol} 즉시 Bearish Divergence: 가격 +{price_change_pct:.2f}% 상승, RSI {rsi_change:.1f}")

        except Exception as e:
            logger.error(f"{symbol} 즉시 RSI 다이버전스 분석 오류: {e}", exc_info=True)
        
        return divergence_signals

    def detect_rsi_divergence(self, symbol: str, timeframe: str = "5m", 
                             rsi_period: int = 14, lookback_periods: int = 20) -> List[str]:
        """RSI 다이버전스를 즉시 감지합니다. 최근 RSI와 비교하여 실시간 알람 생성"""
        divergence_signals = []
        try:
            kst = pytz.timezone('Asia/Seoul')
            current_time = datetime.now(kst)
            
            # 데이터 로드 (충분한 양을 가져와서 RSI 계산)
            df = self.get_candlestick_data(symbol, timeframe, limit=lookback_periods + rsi_period + 10)
            if df is None or len(df) < rsi_period + lookback_periods:
                logger.warning(f"{symbol} 데이터 부족으로 다이버전스 분석 중단")
                return []

            # RSI 계산 및 NaN 값 제거
            df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()
            df = df.dropna().reset_index(drop=True)
            if len(df) < lookback_periods:
                return []

            # 최근 데이터 (현재 vs 과거 비교용)
            current_close = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M')
            
            # lookback_periods 범위에서 비교할 과거 지점들을 찾음
            for i in range(5, min(lookback_periods, len(df) - 1)):  # 최소 5개 이전부터 검사
                past_close = df['close'].iloc[-(i+1)]
                past_rsi = df['rsi'].iloc[-(i+1)]
                
                # Regular Bullish Divergence: 가격은 낮아졌는데 RSI는 높아진 경우
                if current_close < past_close and current_rsi > past_rsi:
                    # RSI 차이가 의미있는 수준인지 확인 (최소 3포인트 차이)
                    if current_rsi - past_rsi >= 3:
                        price_change = ((current_close - past_close) / past_close) * 100
                        rsi_change = current_rsi - past_rsi
                        divergence_signals.append(
                            f"🟢 Regular Bullish Divergence ({timeframe}) - {current_time_str}\n"
                            f"가격: {price_change:.2f}% 하락, RSI: +{rsi_change:.1f} 상승 (최근 {i}캔들 비교)"
                        )
                        logger.info(f"{symbol} 즉시 Regular Bullish Divergence 감지: "
                                   f"가격 {price_change:.2f}% 하락, RSI +{rsi_change:.1f}")
                        break  # 첫 번째 유효한 다이버전스만 알림
                
                # Regular Bearish Divergence: 가격은 높아졌는데 RSI는 낮아진 경우
                elif current_close > past_close and current_rsi < past_rsi:
                    # RSI 차이가 의미있는 수준인지 확인 (최소 3포인트 차이)
                    if past_rsi - current_rsi >= 3:
                        price_change = ((current_close - past_close) / past_close) * 100
                        rsi_change = past_rsi - current_rsi
                        divergence_signals.append(
                            f"🔴 Regular Bearish Divergence ({timeframe}) - {current_time_str}\n"
                            f"가격: +{price_change:.2f}% 상승, RSI: -{rsi_change:.1f} 하락 (최근 {i}캔들 비교)"
                        )
                        logger.info(f"{symbol} 즉시 Regular Bearish Divergence 감지: "
                                   f"가격 +{price_change:.2f}% 상승, RSI -{rsi_change:.1f}")
                        break  # 첫 번째 유효한 다이버전스만 알림

            # Hidden Divergence도 같은 방식으로 검사
            if not divergence_signals:  # Regular 다이버전스가 없는 경우에만 Hidden 검사
                for i in range(5, min(lookback_periods, len(df) - 1)):
                    past_close = df['close'].iloc[-(i+1)]
                    past_rsi = df['rsi'].iloc[-(i+1)]
                    
                    # Hidden Bullish Divergence: 가격은 높아졌는데 RSI는 낮아진 경우 (상승 추세에서)
                    if current_close > past_close and current_rsi < past_rsi:
                        if past_rsi - current_rsi >= 2:  # Hidden은 기준을 조금 낮춤
                            price_change = ((current_close - past_close) / past_close) * 100
                            rsi_change = past_rsi - current_rsi
                            divergence_signals.append(
                                f"🔴 Hidden Bullish Divergence ({timeframe}) - {current_time_str}\n"
                                f"가격: +{price_change:.2f}% 상승, RSI: -{rsi_change:.1f} 하락"
                            )
                            logger.info(f"{symbol} 즉시 Hidden Bullish Divergence 감지: "
                                       f"가격 +{price_change:.2f}% 상승, RSI -{rsi_change:.1f}")
                            break
                    
                    # Hidden Bearish Divergence: 가격은 낮아졌는데 RSI는 높아진 경우 (하락 추세에서)
                    elif current_close < past_close and current_rsi > past_rsi:
                        if current_rsi - past_rsi >= 2:  # Hidden은 기준을 조금 낮춤
                            price_change = ((current_close - past_close) / past_close) * 100
                            rsi_change = current_rsi - past_rsi
                            divergence_signals.append(
                                f"🟠 Hidden Bearish Divergence ({timeframe}) - {current_time_str}\n"
                                f"가격: {price_change:.2f}% 하락, RSI: +{rsi_change:.1f} 상승"
                            )
                            logger.info(f"{symbol} 즉시 Hidden Bearish Divergence 감지: "
                                       f"가격 {price_change:.2f}% 하락, RSI +{rsi_change:.1f}")
                            break

        except Exception as e:
            logger.error(f"{symbol} RSI 다이버전스 분석 오류: {e}", exc_info=True)
        
        # 최종 결과 로깅
        if divergence_signals:
            logger.info(f"{symbol} 즉시 다이버전스 신호 {len(divergence_signals)}개 발견")
        else:
            logger.debug(f"{symbol} 즉시 다이버전스 신호 없음")
        
        return divergence_signals
