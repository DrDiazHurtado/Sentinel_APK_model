import pandas as pd

def compute_previous_day_levels(df: pd.DataFrame):
    """
    Calcula máximos y mínimos del día anterior.
    """
    daily = df.resample("1D").agg({
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna()
    
    prev_high = daily["high"].shift(1)
    prev_low = daily["low"].shift(1)
    prev_close = daily["close"].shift(1)
    
    return prev_high, prev_low, prev_close

def compute_session_levels(df: pd.DataFrame):
    """
    Calcula niveles de la sesión actual (intradía) de forma acumulada.
    """
    df = df.copy()
    df['date'] = df.index.date
    
    # Niveles acumulados por sesión
    df['session_high'] = df.groupby('date')['high'].cummax()
    df['session_low'] = df.groupby('date')['low'].cummin()
    
    # Manejo de activos sin volumen
    volume = df['volume'] if 'volume' in df.columns else pd.Series(0, index=df.index)
    volume = volume.fillna(0)
    
    # VWAP acumulado por sesión
    df['pv'] = df['close'] * volume
    cum_pv = df.groupby('date')['pv'].cumsum()
    cum_v = volume.groupby(df['date']).cumsum()
    
    df['vwap'] = cum_pv / cum_v
    # Si no hay volumen, el VWAP es simplemente el close
    df['vwap'] = df['vwap'].fillna(df['close'])
    
    return df[['session_high', 'session_low', 'vwap']]

class SessionBuilder:
    def process(self, df: pd.DataFrame):
        ph, pl, pc = compute_previous_day_levels(df)
        session_data = compute_session_levels(df)
        
        # Eliminar columnas si ya existen para evitar duplicados en el join
        cols_to_drop = [c for c in session_data.columns if c in df.columns]
        df = df.drop(columns=cols_to_drop).join(session_data, how='left')
        
        # Mapear niveles diarios al intradía con relleno de huecos
        idx_normalized = df.index.normalize()
        df['prev_day_high'] = pd.Series(idx_normalized.map(ph), index=df.index).ffill().bfill()
        df['prev_day_low'] = pd.Series(idx_normalized.map(pl), index=df.index).ffill().bfill()
        df['prev_day_close'] = pd.Series(idx_normalized.map(pc), index=df.index).ffill().bfill()
        
        # Robustez final: si siguen siendo NaN, usar el close actual (mínimo impacto)
        df['prev_day_high'] = df['prev_day_high'].fillna(df['high'])
        df['prev_day_low'] = df['prev_day_low'].fillna(df['low'])
        df['prev_day_close'] = df['prev_day_close'].fillna(df['close'])
        
        return df
