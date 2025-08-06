import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import gate_api
from gate_api.exceptions import ApiException, GateApiException

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
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
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

    def find_pivots(self, data: pd.Series, left_bars: int = 5, right_bars: int = 5) -> Tuple[List[int], List[int]]:
        """피벗 하이/로우를 찾습니다."""
        pivot_lows = []
        pivot_highs = []
        
        for i in range(left_bars, len(data) - right_bars):
            # 피벗 로우 찾기
            is_pivot_low = True
            for j in range(i - left_bars, i + right_bars + 1):
                if j != i and data.iloc[j] <= data.iloc[i]:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                pivot_lows.append(i)
            
            # 피벗 하이 찾기
            is_pivot_high = True
            for j in range(i - left_bars, i + right_bars + 1):
                if j != i and data.iloc[j] >= data.iloc[i]:
                    is_pivot_high = False
                    break
            if is_pivot_high:
                pivot_highs.append(i)
        
        return pivot_lows, pivot_highs

    def detect_rsi_divergence(self, symbol: str, timeframe: str = "5m", 
                             rsi_period: int = 14, lookback_range: Tuple[int, int] = (5, 60),
                             recent_bars_only: int = 5) -> List[str]:
        """RSI 다이버전스를 감지합니다. (최근 봉에서 발생한 것만)"""
        divergence_signals = []
        
        try:
            # 충분한 데이터 가져오기
            df = self.get_candlestick_data(symbol, timeframe, limit=200)
            if df is None or len(df) < 100:
                logger.warning(f"{symbol} 다이버전스 분석을 위한 데이터가 부족합니다.")
                return divergence_signals
            
            # RSI 계산
            rsi_indicator = RSIIndicator(df['close'], window=rsi_period)
            df['rsi'] = rsi_indicator.rsi()
            
            # 피벗 포인트 찾기
            rsi_pivot_lows, rsi_pivot_highs = self.find_pivots(df['rsi'])
            price_pivot_lows, price_pivot_highs = self.find_pivots(df['low'])
            price_high_pivots, _ = self.find_pivots(df['high'])
            
            min_range, max_range = lookback_range
            
            # 최근 봉 범위 계산
            recent_threshold = len(df) - recent_bars_only
            
            # Regular Bullish Divergence 검사 (가격: Lower Low, RSI: Higher Low)
            # 최근 봉에서 발생한 피벗만 확인
            recent_low_pivots = [idx for idx in rsi_pivot_lows if idx >= recent_threshold]
            
            for current_low_idx in recent_low_pivots:
                for prev_low_idx in rsi_pivot_lows:
                    if prev_low_idx >= current_low_idx:  # 이전 피벗이어야 함
                        continue
                        
                    bars_between = current_low_idx - prev_low_idx
                    if min_range <= bars_between <= max_range:
                        # 가격이 Lower Low이고 RSI가 Higher Low인지 확인
                        current_price = df['low'].iloc[current_low_idx]
                        prev_price = df['low'].iloc[prev_low_idx]
                        current_rsi = df['rsi'].iloc[current_low_idx]
                        prev_rsi = df['rsi'].iloc[prev_low_idx]
                        
                        if (current_price < prev_price and  # 가격 Lower Low
                            current_rsi > prev_rsi and      # RSI Higher Low
                            not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                            divergence_signals.append(f"🟢 Regular Bullish Divergence ({timeframe}): 가격 {current_price:.4f} ↓ {prev_price:.4f}, RSI {current_rsi:.2f} ↑ {prev_rsi:.2f}")
                            break
            
            # Regular Bearish Divergence 검사 (가격: Higher High, RSI: Lower High)  
            recent_high_pivots = [idx for idx in rsi_pivot_highs if idx >= recent_threshold]
            
            for current_high_idx in recent_high_pivots:
                for prev_high_idx in rsi_pivot_highs:
                    if prev_high_idx >= current_high_idx:
                        continue
                        
                    bars_between = current_high_idx - prev_high_idx
                    if min_range <= bars_between <= max_range:
                        current_price = df['high'].iloc[current_high_idx]
                        prev_price = df['high'].iloc[prev_high_idx]
                        current_rsi = df['rsi'].iloc[current_high_idx]
                        prev_rsi = df['rsi'].iloc[prev_high_idx]
                        
                        if (current_price > prev_price and  # 가격 Higher High
                            current_rsi < prev_rsi and      # RSI Lower High
                            not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                            divergence_signals.append(f"🔴 Regular Bearish Divergence ({timeframe}): 가격 {current_price:.4f} ↑ {prev_price:.4f}, RSI {current_rsi:.2f} ↓ {prev_rsi:.2f}")
                            break
            
            # Hidden Bullish Divergence 검사 (가격: Higher Low, RSI: Lower Low)
            for current_low_idx in recent_low_pivots:
                for prev_low_idx in rsi_pivot_lows:
                    if prev_low_idx >= current_low_idx:
                        continue
                        
                    bars_between = current_low_idx - prev_low_idx
                    if min_range <= bars_between <= max_range:
                        current_price = df['low'].iloc[current_low_idx]
                        prev_price = df['low'].iloc[prev_low_idx]
                        current_rsi = df['rsi'].iloc[current_low_idx]
                        prev_rsi = df['rsi'].iloc[prev_low_idx]
                        
                        if (current_price > prev_price and  # 가격 Higher Low
                            current_rsi < prev_rsi and      # RSI Lower Low
                            not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                            divergence_signals.append(f"🟡 Hidden Bullish Divergence ({timeframe}): 가격 {current_price:.4f} ↑ {prev_price:.4f}, RSI {current_rsi:.2f} ↓ {prev_rsi:.2f}")
                            break
            
            # Hidden Bearish Divergence 검사 (가격: Lower High, RSI: Higher High)
            for current_high_idx in recent_high_pivots:
                for prev_high_idx in rsi_pivot_highs:
                    if prev_high_idx >= current_high_idx:
                        continue
                        
                    bars_between = current_high_idx - prev_high_idx
                    if min_range <= bars_between <= max_range:
                        current_price = df['high'].iloc[current_high_idx]
                        prev_price = df['high'].iloc[prev_high_idx]
                        current_rsi = df['rsi'].iloc[current_high_idx]
                        prev_rsi = df['rsi'].iloc[prev_high_idx]
                        
                        if (current_price < prev_price and  # 가격 Lower High
                            current_rsi > prev_rsi and      # RSI Higher High
                            not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                            divergence_signals.append(f"🟠 Hidden Bearish Divergence ({timeframe}): 가격 {current_price:.4f} ↓ {prev_price:.4f}, RSI {current_rsi:.2f} ↑ {prev_rsi:.2f}")
                            break
            
        except Exception as e:
            logger.error(f"{symbol} RSI 다이버전스 분석 오류: {e}")
        
        return divergence_signals
