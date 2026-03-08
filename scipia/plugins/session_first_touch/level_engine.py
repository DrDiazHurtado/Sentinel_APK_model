import pandas as pd
import numpy as np

def detect_swings(df: pd.DataFrame, lookback: int = 3):
    """
    Detecta puntos de giro (swings) locales.
    """
    highs = df["high"]
    lows = df["low"]

    # Swing High: High mayor que sus vecinos
    swing_high_mask = (highs > highs.shift(1)) & (highs > highs.shift(-1))
    for i in range(2, lookback + 1):
        swing_high_mask &= (highs > highs.shift(i)) & (highs > highs.shift(-i))
        
    # Swing Low: Low menor que sus vecinos
    swing_low_mask = (lows < lows.shift(1)) & (lows < lows.shift(-1))
    for i in range(2, lookback + 1):
        swing_low_mask &= (lows < lows.shift(i)) & (lows < lows.shift(-i))

    return highs[swing_high_mask], lows[swing_low_mask]

def detect_equal_levels(df: pd.DataFrame, threshold_pct: float = 0.05):
    """
    Detecta niveles de Equal Highs (EQH) o Equal Lows (EQL).
    """
    # Simplificación: buscar máximos/mínimos cercanos en un periodo
    # Esto ayuda a identificar liquidez latente
    pass

class LevelEngine:
    def __init__(self, lookback: int = 5):
        self.lookback = lookback
        
    def get_levels(self, df: pd.DataFrame):
        s_highs, s_lows = detect_swings(df, self.lookback)
        
        # Otros niveles ya vienen de SessionBuilder (VWAP, Prev Day, etc.)
        return {
            "swing_highs": s_highs,
            "swing_lows": s_lows
        }
