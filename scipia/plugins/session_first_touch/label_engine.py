import pandas as pd
import numpy as np

def first_touch_label(df: pd.DataFrame, upper_levels: pd.Series, lower_levels: pd.Series, horizon: int = 8):
    """
    Label Real: Determina qué nivel estructural (PDH, PDL, Session High, etc.) se toca primero.
    1 si toca upper, 0 si toca lower, None si no toca ninguno o toca ambos en la misma barra.
    """
    labels = []
    highs = df['high'].values
    lows = df['low'].values
    uppers = upper_levels.values
    lowers = lower_levels.values

    for i in range(len(df)):
        if i + horizon >= len(df):
            labels.append(None)
            continue
            
        # Ventana de observación futura
        window_highs = highs[i+1 : i+1+horizon]
        window_lows = lows[i+1 : i+1+horizon]
        
        # Niveles objetivos capturados en el momento i
        upper = uppers[i]
        lower = lowers[i]
        
        if pd.isna(upper) or pd.isna(lower):
            labels.append(None)
            continue

        # Encontrar el primer índice donde se cruza el nivel
        hit_up = np.where(window_highs >= upper)[0]
        hit_down = np.where(window_lows <= lower)[0]
        
        first_up = hit_up[0] if len(hit_up) > 0 else 999
        first_down = hit_down[0] if len(hit_down) > 0 else 999
        
        if first_up < first_down:
            labels.append(1)
        elif first_down < first_up:
            labels.append(0)
        else:
            labels.append(None)
            
    return pd.Series(labels, index=df.index)

class LabelEngine:
    def generate(self, df: pd.DataFrame, horizon: int = 12):
        """
        Genera etiquetas resistentes a NaNs y baja volatilidad.
        """
        # Calcular ATR simple
        high_low = df['high'] - df['low']
        atr = high_low.rolling(20).mean().ffill().bfill()
        
        # Desplazamiento mínimo del 0.2% para evitar ruido
        shift = np.maximum(atr * 0.5, df['close'] * 0.002)
        
        upper = df['close'] + shift
        lower = df['close'] - shift
        
        return first_touch_label(df, upper, lower, horizon)
