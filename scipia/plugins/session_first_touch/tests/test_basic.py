import pytest
import pandas as pd
import numpy as np
from scipia.plugins.session_first_touch.bar_normalizer import normalize_bar
from scipia.plugins.session_first_touch.level_engine import detect_swings

def test_normalize_bar():
    bar = normalize_bar("AAPL", pd.Timestamp("2026-03-08 10:00:00"), 150.0, 152.0, 149.0, 151.0, 10000)
    assert bar["symbol"] == "AAPL"
    assert bar["close"] == 151.0

def test_detect_swings():
    # Serie sintética con un pico
    df = pd.DataFrame({
        "high": [100, 101, 105, 101, 100],
        "low": [98, 99, 103, 99, 98]
    })
    s_highs, s_lows = detect_swings(df, lookback=2)
    # El índice 2 es el pico (105)
    assert 2 in s_highs.index
    assert s_highs.loc[2] == 105
