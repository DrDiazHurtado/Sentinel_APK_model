# Definición del universo de activos objetivo y contexto

TARGET_ASSETS = [
    "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOG", "TSLA",
    "ACS.MC",
    "PHAG.L",
    "BTC-USD",
    "EURUSD=X" # Añadido EUR/USD
]

CONTEXT_ASSETS = [
    "SPY", "QQQ", "IWM", "^VIX", "DX-Y.NYB", "^TNX"
]

ALL_ASSETS = TARGET_ASSETS + CONTEXT_ASSETS
