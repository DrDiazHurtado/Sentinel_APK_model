from typing import Dict, Any
import pandas as pd
from datetime import datetime

def normalize_bar(symbol: str, timestamp: datetime, o: float, h: float, l: float, c: float, v: float, 
                  timeframe: str = "15m", source: str = "yahoo", is_regular_session: bool = True) -> Dict[str, Any]:
    """
    Convierte una barra de precios al esquema estándar del plugin.
    """
    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "open": float(o),
        "high": float(h),
        "low": float(l),
        "close": float(c),
        "volume": float(v),
        "timeframe": timeframe,
        "source": source,
        "is_regular_session": is_regular_session
    }

def dataframe_to_normalized_bars(df: pd.DataFrame, symbol: str, timeframe: str = "15m", source: str = "yahoo") -> pd.DataFrame:
    """
    Normaliza un DataFrame completo.
    """
    df = df.copy()
    df["symbol"] = symbol
    df["timeframe"] = timeframe
    df["source"] = source
    # Asumimos que el índice es datetime o tiene columna 'timestamp'
    if "timestamp" not in df.columns:
        df["timestamp"] = df.index
    
    # Detección básica de sesión regular (ejemplo simplificado)
    df["is_regular_session"] = True # Por defecto True, se puede refinar
    
    return df[["symbol", "timestamp", "open", "high", "low", "close", "volume", "timeframe", "source", "is_regular_session"]]
