import pandas as pd
import numpy as np
from .latent_liquidity_field_engine import LatentLiquidityFieldEngine

class FeatureEngine:
    def __init__(self, atr_window: int = 14):
        self.atr_window = atr_window
        self.llf_engine = LatentLiquidityFieldEngine()

    def compute_atr(self, df: pd.DataFrame):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(self.atr_window).mean()

    def process(self, df: pd.DataFrame, context_dfs: dict = None, use_llf: bool = True, last_only: bool = False):
        """
        Optimización Crítica: Si last_only=True, solo calcula LLF para la última fila (Inferencia).
        """
        df = df.copy()
        atr = self.compute_atr(df)
        # Robustez: ATR no puede ser cero ni NaN para las divisiones
        min_atr = df['close'] * 1e-5
        df['atr'] = atr.fillna(min_atr).clip(lower=min_atr)
        
        # Features Estructurales
        df['dist_to_prev_high_atr'] = (df['close'] - df['prev_day_high']) / df['atr']
        df['dist_to_prev_low_atr'] = (df['close'] - df['prev_day_low']) / df['atr']
        df['dist_to_session_high_atr'] = (df['close'] - df['session_high']) / df['atr']
        df['dist_to_session_low_atr'] = (df['close'] - df['session_low']) / df['atr']
        df['dist_to_vwap_atr'] = (df['close'] - df['vwap']) / df['atr']
        df['range_atr_ratio'] = (df['high'] - df['low']) / df['atr']

        # Features de Gap y Sesión
        df['date_tmp'] = df.index.date
        df['is_first_bar'] = df['date_tmp'] != pd.Series(df['date_tmp']).shift(1).values
        
        atr_prev = df['atr'].shift(1).bfill()
        # Calculamos el gap en la apertura respecto al cierre previo
        gap_size = np.where(df['is_first_bar'], (df['open'] - df['prev_day_close']) / atr_prev, np.nan)
        df['gap_size_atr'] = pd.Series(gap_size, index=df.index).ffill().fillna(0)
        
        gap_dir = np.where(df['is_first_bar'], np.sign(df['open'] - df['prev_day_close']), np.nan)
        df['gap_direction'] = pd.Series(gap_dir, index=df.index).ffill().fillna(0)
        
        # Umbral relativo de > 0.5 ATR para considerar gap
        is_gap = np.where(df['is_first_bar'], np.abs((df['open'] - df['prev_day_close']) / atr_prev) > 0.5, np.nan)
        df['is_gap_open'] = pd.Series(is_gap, index=df.index).ffill().fillna(False)
        
        session_open = np.where(df['is_first_bar'], df['open'], np.nan)
        df['session_open_price'] = pd.Series(session_open, index=df.index).ffill()
        
        gap_diff = df['prev_day_close'] - df['session_open_price']
        df['fill_progress'] = np.where(gap_diff != 0, (df['close'] - df['session_open_price']) / gap_diff, 0)
        
        df = df.drop(columns=['date_tmp'])

        if use_llf:
            llf_features = []
            # Rango de filas a procesar
            start_idx = len(df) - 1 if last_only else 0
            
            for i in range(len(df)):
                if i < start_idx or i < 100: 
                    llf_features.append({f"llf_{k}": np.nan for k in ["mass_asymmetry", "peak_dist", "mass_above", "mass_below", "gradient_local"]})
                    continue
                
                current_levels = [df['prev_day_high'].iloc[i], df['prev_day_low'].iloc[i], df['vwap'].iloc[i]]
                
                # Construir campo sobre ventana de lookback
                try:
                    grid, llf = self.llf_engine.build_llf(
                        df.iloc[max(0, i-100):i+1], 
                        df['close'].iloc[i], 
                        df['atr'].iloc[i], 
                        current_levels
                    )
                    llf_features.append(self.llf_engine.extract_features(grid, llf, df['close'].iloc[i]))
                except Exception:
                    llf_features.append({f"llf_{k}": np.nan for k in ["mass_asymmetry", "peak_dist", "mass_above", "mass_below", "gradient_local"]})
            
            llf_df = pd.DataFrame(llf_features, index=df.index)
            df = pd.concat([df, llf_df], axis=1)
            
        # Solo dropear NaNs en las columnas que usamos como features o target
        feature_cols = [c for c in df.columns if 'dist_to' in c or 'llf_' in c or 'range_atr' in c]
        return df.dropna(subset=feature_cols)
