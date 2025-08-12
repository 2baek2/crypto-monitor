import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import gate_api
from gate_api.exceptions import ApiException, GateApiException
import pytz

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """기술적 분석을 수행하는 클래스"""
    
    def __init__(self, spot_api, futures_api=None, market_type='spot'):
        self.spot_api = spot_api
        self.futures_api = futures_api
        self.market_type = market_type
        
    def get_candlestick_data(self, symbol: str, interval: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """캔들스틱 데이터를 가져와서 DataFrame으로 변환합니다."""
        try:
            # Gate.io 간격 매핑
            interval_mapping = {
                "1m": "1m",
                "5m": "5m", 
                "15m": "15m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d"
            }
            
            gate_interval = interval_mapping.get(interval, "5m")
            
            # 시장 타입에 따라 다른 API 사용
            if self.market_type == 'futures' and self.futures_api:
                candlesticks = self._get_futures_candlesticks(symbol, gate_interval, limit)
            else:
                candlesticks = self._get_spot_candlesticks(symbol, gate_interval, limit)
            
            if not candlesticks:
                logger.warning(f"{symbol} {interval} 캔들스틱 데이터가 없습니다.")
                return None
                
            # DataFrame으로 변환
            data = []
            for candle in candlesticks:
                # futures와 spot의 데이터 구조가 다를 수 있음
                if self.market_type == 'futures':
                    # Futures candlestick은 객체일 수 있음
                    if hasattr(candle, 't'):  # 객체 형태
                        data.append({
                            'timestamp': int(candle.t),
                            'open': float(candle.o),
                            'high': float(candle.h),
                            'low': float(candle.l),
                            'close': float(candle.c),
                            'volume': float(candle.v) if hasattr(candle, 'v') else 0
                        })
                    else:  # 리스트 형태
                        data.append({
                            'timestamp': int(candle[0]),
                            'open': float(candle[5]),
                            'high': float(candle[3]),
                            'low': float(candle[4]),
                            'close': float(candle[2]),
                            'volume': float(candle[1])
                        })
                else:
                    # Spot은 기존 방식 사용
                    data.append({
                        'timestamp': int(candle[0]),
                        'open': float(candle[5]),
                    'high': float(candle[3]),
                    'low': float(candle[4]),
                    'close': float(candle[2]),
                    'volume': float(candle[1])
                })
            
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.debug(f"{symbol} {interval} 데이터 {len(df)}개 로드 완료")
            return df
            
        except (ApiException, GateApiException) as e:
            logger.error(f"{symbol} {interval} 캔들스틱 데이터 조회 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"{symbol} {interval} 데이터 처리 오류: {e}")
            return None

    def _get_spot_candlesticks(self, symbol: str, interval: str, limit: int):
        """스팟 캔들스틱 데이터를 조회합니다."""
        return self.spot_api.list_candlesticks(
            currency_pair=symbol,
            interval=interval,
            limit=limit
        )

    def _get_futures_candlesticks(self, symbol: str, interval: str, limit: int):
        """퓨처스 캔들스틱 데이터를 조회합니다."""
        # 퓨처스 심볼을 contract로 변환 (예: BTC_USDT -> BTC_USDT)
        # Gate.io futures는 settle 파라미터가 필요할 수 있음
        settle = 'usdt'  # 기본 결제 통화
        return self.futures_api.list_futures_candlesticks(
            settle=settle,
            contract=symbol,
            interval=interval,
            limit=limit
        )
    
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

    def detect_rsi_divergence(self, symbol: str, timeframe: str = "5m", 
                             rsi_period: int = 14, left_bars: int = 5, right_bars: int = 5,
                             lookback_range: Tuple[int, int] = (5, 60)) -> List[str]:
        """RSI 다이버전스를 감지합니다. (TradingView Pine Script 로직 기반)"""
        divergence_signals = []
        try:
            kst = pytz.timezone('Asia/Seoul')
            min_range, max_range = lookback_range
            
            # 데이터 로드 (계산에 필요한 충분한 양)
            df = self.get_candlestick_data(symbol, timeframe, limit=max_range + left_bars + right_bars + 100)
            if df is None or len(df) < rsi_period + max_range:
                logger.warning(f"{symbol} 데이터 부족으로 다이버전스 분석 중단")
                return []

            # RSI 계산 및 NaN 값 제거
            df['rsi'] = RSIIndicator(df['close'], window=rsi_period).rsi()
            df = df.dropna().reset_index(drop=True)
            if len(df) < max_range + left_bars:
                return []

            # 피벗 포인트 찾기
            rsi_pivot_lows, rsi_pivot_highs = self.find_pivots(df['rsi'], left_bars, right_bars)
            price_pivot_lows, price_pivot_highs = self.find_pivots(df['low'], left_bars, right_bars)
            price_high_pivots, _ = self.find_pivots(df['high'], left_bars, right_bars)


            # --- 다이버전스 검사 (가장 최근에 형성된 2개의 피벗을 기준) ---
            # Regular Bullish: Price Lower Low, RSI Higher Low
            if len(rsi_pivot_lows) >= 2 and len(price_pivot_lows) >= 2:
                p2_idx, p1_idx = rsi_pivot_lows[-1], rsi_pivot_lows[-2]
                price_p2_idx, price_p1_idx = price_pivot_lows[-1], price_pivot_lows[-2]
                if min_range <= (p2_idx - p1_idx) <= max_range:
                    if df['low'].iloc[price_p2_idx] < df['low'].iloc[price_p1_idx] and df['rsi'].iloc[p2_idx] > df['rsi'].iloc[p1_idx]:
                        timestamp = df['datetime'].iloc[p2_idx].astimezone(kst).strftime('%Y-%m-%d %H:%M')
                        divergence_signals.append(f"🟢 Regular Bullish Divergence ({timeframe}) - {timestamp}")

            # Hidden Bullish: Price Higher Low, RSI Lower Low
            if len(rsi_pivot_lows) >= 2 and len(price_pivot_lows) >= 2:
                p2_idx, p1_idx = rsi_pivot_lows[-1], rsi_pivot_lows[-2]
                price_p2_idx, price_p1_idx = price_pivot_lows[-1], price_pivot_lows[-2]
                if min_range <= (p2_idx - p1_idx) <= max_range:
                    if df['low'].iloc[price_p2_idx] > df['low'].iloc[price_p1_idx] and df['rsi'].iloc[p2_idx] < df['rsi'].iloc[p1_idx]:
                        timestamp = df['datetime'].iloc[p2_idx].astimezone(kst).strftime('%Y-%m-%d %H:%M')
                        divergence_signals.append(f"🟡 Hidden Bullish Divergence ({timeframe}) - {timestamp}")

            # Regular Bearish: Price Higher High, RSI Lower High
            if len(rsi_pivot_highs) >= 2 and len(price_high_pivots) >= 2:
                p2_idx, p1_idx = rsi_pivot_highs[-1], rsi_pivot_highs[-2]
                price_p2_idx, price_p1_idx = price_high_pivots[-1], price_high_pivots[-2]
                if min_range <= (p2_idx - p1_idx) <= max_range:
                    if df['high'].iloc[price_p2_idx] > df['high'].iloc[price_p1_idx] and df['rsi'].iloc[p2_idx] < df['rsi'].iloc[p1_idx]:
                        timestamp = df['datetime'].iloc[p2_idx].astimezone(kst).strftime('%Y-%m-%d %H:%M')
                        divergence_signals.append(f"🔴 Regular Bearish Divergence ({timeframe}) - {timestamp}")

            # Hidden Bearish: Price Lower High, RSI Higher High
            if len(rsi_pivot_highs) >= 2 and len(price_high_pivots) >= 2:
                p2_idx, p1_idx = rsi_pivot_highs[-1], rsi_pivot_highs[-2]
                price_p2_idx, price_p1_idx = price_high_pivots[-1], price_high_pivots[-2]
                if min_range <= (p2_idx - p1_idx) <= max_range:
                    if df['high'].iloc[price_p2_idx] < df['high'].iloc[price_p1_idx] and df['rsi'].iloc[p2_idx] > df['rsi'].iloc[p1_idx]:
                        timestamp = df['datetime'].iloc[p2_idx].astimezone(kst).strftime('%Y-%m-%d %H:%M')
                        divergence_signals.append(f"🟠 Hidden Bearish Divergence ({timeframe}) - {timestamp}")

        except Exception as e:
            logger.error(f"{symbol} RSI 다이버전스 분석 오류: {e}", exc_info=True)
        
        return list(set(divergence_signals)) # 중복된 신호 제거 후 반환
