import numpy as np
from typing import Dict, Optional

class OrderGenerator:
    """
    Convierte una predicción de First-Touch en una orden ejecutable con gestión de riesgo.
    Ajustado para devolver motivos de rechazo explícitos.
    """
    def __init__(self, capital: float = 24000, risk_per_trade_pct: float = 0.01, max_risk_eur: float = 100):
        self.capital = capital
        self.risk_per_trade = min(capital * risk_per_trade_pct, max_risk_eur)
        self.min_notional = 2500
        
    def get_market_costs(self, symbol: str) -> Dict:
        if ".MC" in symbol:
            return {"commission_fixed": 8.0, "slippage_atr_pct": 0.10}
        elif "USD" in symbol or "=X" in symbol:
            return {"commission_fixed": 2.0, "slippage_atr_pct": 0.05}
        else:
            return {"commission_fixed": 1.5, "slippage_atr_pct": 0.05}

    def calculate_trade_geometry(self, symbol: str, current_price: float, target_price: float, 
                                 llf_grid: np.ndarray, llf_field: np.ndarray, direction: str,
                                 risk_multiplier: float = 1.0) -> Dict:
        costs = self.get_market_costs(symbol)
        
        # Ajuste de riesgo para modos degradados/provisionales
        current_risk_per_trade = self.risk_per_trade * risk_multiplier
        
        if direction == "UP":
            sl_mask = llf_grid < current_price
            if not any(sl_mask): return {"status": "NO_STRUCTURAL_SL"}
            sl_price = llf_grid[sl_mask][np.argmax(llf_field[sl_mask])]
            sl_price *= 0.998
        else:
            sl_mask = llf_grid > current_price
            if not any(sl_mask): return {"status": "NO_STRUCTURAL_SL"}
            sl_price = llf_grid[sl_mask][np.argmax(llf_field[sl_mask])]
            sl_price *= 1.002

        atr_local = abs(target_price - current_price) / 4.0 if abs(target_price - current_price) > 0 else 0.1
        est_slippage = atr_local * costs["slippage_atr_pct"]
        
        effective_risk = abs(current_price - sl_price) + est_slippage
        effective_reward = abs(target_price - current_price) - est_slippage
        
        if effective_risk <= 0: return {"status": "INVALID_RISK"}
        rr = effective_reward / effective_risk
        
        if rr < 2.0:
            return {"status": "LOW_RR", "rr": round(rr, 2)}

        shares = int(current_risk_per_trade / effective_risk)
        if shares <= 0:
            return {"status": "RISK_TOO_HIGH_FOR_1_SHARE"}

        notional = shares * current_price
        
        total_comm = costs["commission_fixed"] * 2
        if total_comm > (current_risk_per_trade * 0.25):
             return {"status": "HIGH_FRICTION"}

        # En modo provisional, relajamos el notional mínimo si el multiplicador < 1
        min_notional = self.min_notional * risk_multiplier
        if notional < min_notional:
            return {"status": "LOW_NOTIONAL"}

        return {
            "status": "APPROVED",
            "symbol": symbol,
            "direction": direction,
            "entry": round(current_price, 2),
            "tp": round(target_price, 2),
            "sl": round(sl_price, 2),
            "rr": round(rr, 2),
            "shares": shares,
            "notional": round(notional, 2),
            "risk_total": round(shares * effective_risk, 2)
        }
