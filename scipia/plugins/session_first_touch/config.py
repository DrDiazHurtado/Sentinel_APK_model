# Configuración interna del plugin session_first_touch

class Config:
    HORIZON_BARS = [2, 4, 6, 8]
    ATR_WINDOW = [10, 14, 20]
    VOL_WINDOW = [10, 20, 40]
    
    TF_WEIGHTS = {
        "M15": 1.0,
        "H1": 0.7,
        "D1": 0.4
    }
    
    DEFAULT_THRESHOLD = 0.60
    DECAY_HALF_LIFE_DAYS = [5, 10, 20]
    
    # Fuentes de datos
    DATA_SOURCES = ["ibkr", "yahoo"]
    
    # Umbrales de robustez
    SLIPPAGE_STRESS = 1.5  # +50%
    THRESHOLD_STRESS = 0.03
