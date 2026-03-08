import pandas as pd
import yfinance as yf
import os
import yaml
import numpy as np
from datetime import datetime, timedelta
import pytz

CACHE_DIR = "data_lake/intraday_cache"

def load_config():
    with open("scipia/plugins/session_first_touch/config.yaml", "r") as f:
        return yaml.safe_load(f)

def fetch_yahoo_history(symbol: str, period: str = "60d", interval: str = "15m") -> dict:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return {'df': pd.DataFrame(), 'status': 'Y_EMPTY'}
        
        df.columns = [c.lower() for c in df.columns]
        # Forzar DatetimeIndex UTC
        df.index = pd.to_datetime(df.index, utc=True)
        
        now_utc = datetime.now(pytz.UTC)
        if (df.index[-1] + timedelta(minutes=15)) > now_utc:
            df = df.iloc[:-1]
            status = 'Y_OK_CLEAN'
        else:
            status = 'Y_OK'
        return {'df': df, 'status': status}
    except Exception as e:
        return {'df': pd.DataFrame(), 'status': f'Y_ERR:{str(e)[:10]}'}

class DataLoader:
    def __init__(self, symbol: str):
        self.symbol = symbol
        safe_name = symbol.replace('=', '_').replace('.', '_').replace('-', '_')
        self.cache_path = os.path.join(CACHE_DIR, f"{safe_name}_15m.parquet")
        self.last_df = pd.DataFrame()
        self.current_trace = "INIT"

    def get_data(self) -> pd.DataFrame:
        # 1. Cargar Cache con validación de tipo de índice
        if os.path.exists(self.cache_path) and self.last_df.empty:
            try:
                self.last_df = pd.read_parquet(self.cache_path)
                self.last_df.index = pd.to_datetime(self.last_df.index, utc=True)
                self.current_trace = "CACHE"
            except: 
                self.last_df = pd.DataFrame()

        now_utc = datetime.now(pytz.UTC)
        last_ts = self.last_df.index[-1] if not self.last_df.empty else datetime.min.replace(tzinfo=pytz.UTC)
        
        # Sync si es necesario
        if (now_utc - last_ts) >= timedelta(minutes=15) or self.last_df.empty:
            res = fetch_yahoo_history(self.symbol, period="60d" if self.last_df.empty else "5d")
            self.current_trace = res['status']
            if not res['df'].empty:
                combined = pd.concat([self.last_df, res['df']])
                combined = combined[~combined.index.duplicated(keep='last')].sort_index()
                combined.index = pd.to_datetime(combined.index, utc=True)
                self.last_df = combined
                self.last_df.to_parquet(self.cache_path)

        # Garantizar DatetimeIndex antes de retornar
        if not self.last_df.empty and not isinstance(self.last_df.index, pd.DatetimeIndex):
            self.last_df.index = pd.to_datetime(self.last_df.index, utc=True)
            
        self.last_df.attrs['source_trace'] = self.current_trace
        return self.last_df
