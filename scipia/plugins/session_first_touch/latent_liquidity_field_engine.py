import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

def gaussian_kernel(x, bw):
    return np.exp(-0.5 * (x / bw) ** 2)

class LatentLiquidityFieldEngine:
    """
    Estima el campo latente de liquidez (LLF) sobre el eje de precio usando solo OHLCV.
    """
    def __init__(self, grid_width_atr: float = 3.0, grid_step_pct_atr: float = 0.05):
        self.grid_width_atr = grid_width_atr
        self.grid_step_pct_atr = grid_step_pct_atr

    def create_grid(self, current_price: float, atr: float) -> np.ndarray:
        step = atr * self.grid_step_pct_atr
        if step <= 0: step = 0.01
        
        lower = current_price - (self.grid_width_atr * atr)
        upper = current_price + (self.grid_width_atr * atr)
        
        return np.arange(lower, upper, step)

    def compute_vp_density(self, df: pd.DataFrame, grid: np.ndarray, bandwidth: float = 0.2) -> np.ndarray:
        # Usar lookback de las últimas 100 barras para el perfil de volumen
        recent = df.tail(100)
        if recent.empty: return np.zeros(len(grid))
        
        # Vectorización: diffs [grid_size, lookback]
        diffs = grid[:, np.newaxis] - recent['close'].values
        kernels = gaussian_kernel(diffs, bandwidth)
        density = (kernels * recent['volume'].values).sum(axis=1)
        
        return density / (density.sum() + 1e-9)

    def compute_tp_profile(self, df: pd.DataFrame, grid: np.ndarray) -> np.ndarray:
        recent = df.tail(100)
        if recent.empty: return np.zeros(len(grid))
        
        # Vectorización: grid_size x lookback
        lows = recent['low'].values
        highs = recent['high'].values
        inside = (grid[:, np.newaxis] >= lows) & (grid[:, np.newaxis] <= highs)
        score = inside.sum(axis=1).astype(float)
            
        return score / (score.sum() + 1e-9)

    def compute_stop_cluster_score(self, grid: np.ndarray, levels: List[float], atr: float) -> np.ndarray:
        lvls = np.array([lvl for lvl in levels if not pd.isna(lvl)])
        if len(lvls) == 0: return np.zeros(len(grid))
        
        bw = atr * 0.1 # Suavizado cerca de niveles
        diffs = grid[:, np.newaxis] - lvls
        score = gaussian_kernel(diffs, bw).sum(axis=1)
            
        return score / (score.max() + 1e-9) if score.max() > 0 else score

    def build_llf(self, df: pd.DataFrame, current_price: float, atr: float, levels: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        grid = self.create_grid(current_price, atr)
        
        vp = self.compute_vp_density(df, grid)
        tp = self.compute_tp_profile(df, grid)
        stops = self.compute_stop_cluster_score(grid, levels, atr)
        
        # Simplificación para el campo combinado: 
        # LLF = VP + TP + STOPS - (1 - (VP + TP))
        # Nota: a6 (void) es inversamente proporcional a la permanencia
        void = 1.0 - (vp + tp) / ((vp + tp).max() + 1e-9)
        
        llf = (1.0 * vp + 0.7 * tp + 1.2 * stops - 0.5 * void)
        llf = (llf - llf.min()) / (llf.max() - llf.min() + 1e-9)
        
        return grid, llf

    def extract_features(self, grid: np.ndarray, llf: np.ndarray, current_price: float) -> Dict[str, float]:
        """
        Convierte el campo latente en features tabulares.
        """
        if len(llf) < 3:
            return {f"llf_{k}": 0.0 for k in ["mass_asymmetry", "peak_dist", "mass_above", "mass_below", "gradient_local"]}

        above_mask = grid > current_price
        below_mask = grid < current_price
        
        mass_above = llf[above_mask].sum()
        mass_below = llf[below_mask].sum()
        
        # Localización de picos
        peak_idx = np.argmax(llf)
        peak_dist = (grid[peak_idx] - current_price)
        
        # Gradiente local con protección de bordes
        idx = np.abs(grid - current_price).argmin()
        idx_prev = max(0, idx - 1)
        idx_next = min(len(llf) - 1, idx + 1)
        gradient = llf[idx_next] - llf[idx_prev]
        
        return {
            "llf_mass_asymmetry": (mass_above - mass_below) / (mass_above + mass_below + 1e-9),
            "llf_peak_dist": peak_dist,
            "llf_mass_above": mass_above,
            "llf_mass_below": mass_below,
            "llf_gradient_local": gradient
        }
