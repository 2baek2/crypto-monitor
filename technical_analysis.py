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
    
    def __init__(self, spot_api):
        self.spot_api = spot_api
        
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
            
            # 캔들스틱 데이터 조회
            candlesticks = self.spot_api.list_candlesticks(
                currency_pair=symbol,
                interval=gate_interval,
                limit=limit
            )
            
            if not candlesticks:
                logger.warning(f"{symbol} {interval} 캔들스틱 데이터가 없습니다.")
                return None
                
            # DataFrame으로 변환
            data = []
            for candle in candlesticks:
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
