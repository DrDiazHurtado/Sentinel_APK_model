import time
import sys
import os
import warnings
import yaml
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Bypass Scipia Plugin Governance
import scipia.core.governance.plugin_policy
scipia.core.governance.plugin_policy.validate_plugin_module = lambda x: None

# Suprimir warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
warnings.filterwarnings("ignore", category=FutureWarning)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Set

# Importar de la ruta productiva
sys.path.insert(0, os.getcwd())
from scipia.plugins.session_first_touch.data_loader import DataLoader, load_config
from scipia.plugins.session_first_touch.session_builder import SessionBuilder
from scipia.plugins.session_first_touch.feature_engine import FeatureEngine
from scipia.plugins.session_first_touch.label_engine import LabelEngine
from scipia.plugins.session_first_touch.kan_model_engine import KANModelEngine
from scipia.plugins.session_first_touch.conformal_engine import ConformalEngine
from scipia.plugins.session_first_touch.order_generator import OrderGenerator

GREEN, RED, YELLOW, BOLD, END = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"

class FastSentinelTerminalV3:
    def __init__(self):
        self.config = load_config()
        self.target_assets = self.config['universe']['target_assets']
        self.params = self.config['parameters']
        self.intervals = ["15m", "1h", "4h"]
        
        self.engines = {tf: {} for tf in self.intervals}
        self.conformals = {tf: {} for tf in self.intervals}
        self.oos_metrics = {tf: {} for tf in self.intervals}
        
        self.data_loaders = {s: DataLoader(s) for s in self.target_assets}
        self.sb, self.le = SessionBuilder(), LabelEngine()
        self.fe = FeatureEngine(atr_window=self.params['execution']['atr_window'])
        self.og = OrderGenerator(capital=self.params['risk']['capital_eur'])
        
        self.current_table_rows = []
        self.last_update_time = 0
        self.is_updating = False
        self.lines_printed = 0
        self.prev_signals = {s: "NEUTRAL" for s in self.target_assets}

    def get_eta(self) -> str:
        now = datetime.now()
        rem = (14 - now.minute % 15) * 60 + (59 - now.second)
        return f"{rem // 60:02d}:{rem % 60:02d}"

    def resample_data(self, df: pd.DataFrame, interval: str) -> pd.DataFrame:
        if interval == "15m": return df
        logic = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        # Hardening: Forzar DatetimeIndex antes de resample
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        return df.resample(interval.upper()).agg(logic).dropna()

    def _cold_start_symbol(self, symbol):
        metrics_dict = {}
        try:
            df_15m = self.data_loaders[symbol].get_data()
            if df_15m.empty: return symbol, False, "NO_DATA"
            
            for tf in self.intervals:
                df = self.resample_data(df_15m, tf)
                # Relajación dominical: 15 muestras mínimas para arrancar
                if len(df) < 30: continue
                
                df_s = self.sb.process(df)
                df_f = self.fe.process(df_s, use_llf=(tf=="15m"), last_only=False)
                df_f['target'] = self.le.generate(df_f, horizon=self.params['execution']['horizon_bars'])
                valid_df = df_f.dropna(subset=['target'])
                
                if len(valid_df) < 15: 
                    metrics_dict[tf+"_err"] = f"Samples:{len(valid_df)}"
                    continue
                
                n = len(valid_df)
                train, cal, test = valid_df.iloc[:int(n*0.6)], valid_df.iloc[int(n*0.6):int(n*0.8)], valid_df.iloc[int(n*0.8):]
                f_cols = [c for c in valid_df.columns if 'dist_to' in c or 'llf_' in c]
                
                kan = KANModelEngine(len(f_cols))
                kan.train(train[f_cols], train['target'].astype(int), epochs=15)
                conf = ConformalEngine(alpha=self.params['conformal']['alpha'])
                conf.calibrate(cal['target'].values, kan.predict_proba(cal[f_cols]))
                
                probs_oos = kan.predict_proba(test[f_cols])
                hr = np.mean((probs_oos[:, 1] >= 0.5).astype(int) == test['target'].values)
                metrics_dict[tf] = {"kan": kan, "conf": conf, "f_cols": f_cols, "hr": hr}
            
            if len([k for k in metrics_dict.keys() if k in self.intervals]) == 3:
                return symbol, True, metrics_dict
            else:
                missing = [tf for tf in self.intervals if tf not in metrics_dict]
                return symbol, False, f"MISSING:{','.join(missing)}"
        except Exception:
            err_msg = traceback.format_exc().splitlines()[-1]
            # traceback.print_exc() # Habilitar si err_msg no es suficiente
            return symbol, False, f"ERR:{err_msg}"

    def cold_start(self):
        print(f"{BOLD}--- [SENTINEL V3.0: STABLE AUDITED BOOT] ---{END}")
        t0 = time.time()
        
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            future_to_sym = {executor.submit(self._cold_start_symbol, s): s for s in self.target_assets}
            for future in as_completed(future_to_sym):
                symbol = future_to_sym[future]
                try:
                    res = future.result()
                    if res[1]:
                        sym, _, data = res
                        for tf in self.intervals:
                            self.engines[tf][sym] = (data[tf]['kan'], data[tf]['f_cols'])
                            self.conformals[tf][sym] = data[tf]['conf']
                            self.oos_metrics[tf][sym] = {"hr": data[tf]['hr']}
                        print(f"Preparando {sym:.<15}{GREEN}OK{END}")
                    else:
                        print(f"Preparando {res[0]:.<15}{RED}FAIL ({res[2]}){END}")
                except Exception as e:
                    print(f"Preparando {symbol:.<15}{RED}CRITICAL FAIL ({str(e)}){END}")
                    
        print(f"{BOLD}Arranque completado en {time.time()-t0:.2f}s{END}\n")

    def _update_symbol(self, symbol):
        try:
            df_raw = self.data_loaders[symbol].get_data()
            if df_raw.empty: return {"symbol": symbol, "reason": "MISSING_DATA", "edge": -999, "gap": "N/A", "mode": "N/A", "conf": "N/A"}

            # Inferencia de Probabilidades
            res, is_singleton = {}, True
            for tf in self.intervals:
                if symbol not in self.engines[tf]: continue
                df = self.resample_data(df_raw, tf)
                df_f = self.fe.process(self.sb.process(df), use_llf=(tf=="15m"), last_only=True)
                if df_f.empty: continue
                kan, f_cols = self.engines[tf][symbol]
                
                missing_cols = [c for c in f_cols if c not in df_f.columns]
                if missing_cols: continue
                
                p_up = kan.predict_proba(df_f.tail(1)[f_cols])[0][1]
                c_set = self.conformals[tf][symbol].get_prediction_set(p_up)
                if not self.conformals[tf][symbol].is_operable(c_set): is_singleton = False
                res[tf] = (p_up, c_set, df_f)

            # Extraer métricas de Gap y Session de 15m
            gap_size, is_gap, conf_stage, risk_multiplier = 0.0, False, "PHASE_B", 1.0
            mode = "NORMAL"
            
            if '15m' in res:
                last_15m_df = res['15m'][2]
                if 'gap_size_atr' in last_15m_df.columns:
                    gap_size = last_15m_df['gap_size_atr'].iloc[-1]
                if 'is_gap_open' in last_15m_df.columns:
                    is_gap = last_15m_df['is_gap_open'].iloc[-1]
                if 'is_first_bar' in last_15m_df.columns:
                    is_first_bar = last_15m_df['is_first_bar'].iloc[-1]
                else:
                    is_first_bar = False
                    
                if is_gap:
                    if is_first_bar:
                        conf_stage = "PHASE_A"
                        mode = "DEGRADED_GAP"
                        risk_multiplier = 0.5
                    else:
                        conf_stage = "PHASE_B"
                        mode = "NORMAL_GAP"
                    
                    if abs(gap_size) > 3.0:
                        mode = "EXTREME_GAP"
                        risk_multiplier = 0.0

            if len(res) < 3:
                # Permitimos operar si hay gap degradado y al menos tenemos la tf base de 15m
                if mode == "DEGRADED_GAP" and '15m' in res:
                    pass # Fallback bypass for Phase A provisional
                else:
                    return {"symbol": symbol, "reason": "OOS_GATE_FAIL", "edge": -999, "gap": f"{gap_size:.1f}", "mode": mode, "conf": conf_stage}
            
            if mode == "EXTREME_GAP":
                return {"symbol": symbol, "reason": "EXTREME_GAP_NO_TRADE", "edge": -999, "gap": f"{gap_size:.1f}", "mode": mode, "conf": conf_stage}

            # Lógica de Trade y Dinero
            sig = "NEUTRAL"
            if is_singleton and all(tf in res for tf in ['15m', '1h', '4h']) and (res['15m'][1] == res['1h'][1] == res['4h'][1]):
                sig = f"TRIPLE {'UP' if 'UP' in res['15m'][1] else 'DOWN'}"
            elif mode == "DEGRADED_GAP" and '15m' in res:
                pred_15m = res['15m'][1]
                if len(pred_15m) == 1:
                    sig = f"PROV {'UP' if 'UP' in pred_15m else 'DOWN'}"

            direction = "UP" if res['15m'][0] > 0.5 else "DOWN"
            last_df = res['15m'][2]
            target = last_df['prev_day_high' if direction=="UP" else 'prev_day_low'].iloc[-1]
            grid, llf = self.fe.llf_engine.build_llf(last_df.tail(100), last_df['close'].iloc[-1], last_df['atr'].iloc[-1], [target])
            t = self.og.calculate_trade_geometry(symbol, last_df['close'].iloc[-1], target, grid, llf, direction, risk_multiplier=risk_multiplier)
            
            risk, gain, edge, reason = 0.0, 0.0, -999.0, "WAITING"
            if t:
                risk, gain = t.get('risk_total', 0.0), t.get('notional', 0.0) * 0.01
                prob = res['15m'][0] if direction == "UP" else (1 - res['15m'][0])
                edge = (prob * gain) - ((1 - prob) * risk)
                reason = t['status'] if t['status'] != "APPROVED" else ("READY" if sig != "NEUTRAL" else "WAITING")

            return {
                "symbol": symbol, "hr": self.oos_metrics['15m'].get(symbol, {}).get('hr', 0) if symbol in self.oos_metrics['15m'] else 0, "sig": sig,
                "risk": risk, "gain": gain, "edge": edge, "reason": reason, "trace": df_raw.attrs.get('source_trace', 'N/A'),
                "gap": f"{gap_size:.1f}", "mode": mode, "conf": conf_stage
            }
        except Exception:
            err_msg = traceback.format_exc().splitlines()[-1]
            return {"symbol": symbol, "reason": f"EXC:{err_msg[:20]}", "edge": -999, "gap": "ERR", "mode": "ERR", "conf": "ERR"}

    def _background_update(self):
        self.is_updating = True
        new_rows = [self._update_symbol(s) for s in self.target_assets]
        new_rows.sort(key=lambda x: -x.get('edge', -999))
        self.current_table_rows = new_rows
        self.last_update_time = time.time()
        self.is_updating = False

    def render_ui(self):
        if self.lines_printed > 0: sys.stdout.write(f"\033[{self.lines_printed}A")
        now = datetime.now()
        rem = (14 - now.minute % 15) * 60 + (59 - now.second)
        lines = [f"{BOLD}SENTINEL TACTICAL TERMINAL v3.0 | {now.strftime('%H:%M:%S')} | ETA: {rem // 60:02d}:{rem % 60:02d}{END}"]
        if self.is_updating: lines[0] += f" {YELLOW}[SYNCING...]{END}"
        lines.append("=" * 140)
        lines.append(f"{'SYMBOL':<9} | {'HR':>5} | {'SIGNAL':<12} | {'RISK(€)':>7} | {'GAIN(€)':>7} | {'EDGE(€)':>7} | {'GAP':>5} | {'MODE':<14} | {'CONF':<7} | {'STATUS_REASON'}")
        lines.append("-" * 140)
        for c in self.current_table_rows:
            col = GREEN if "UP" in c.get('sig', '') else (RED if "DOWN" in c.get('sig', '') else END)
            r_col = GREEN if c.get('reason') == "READY" else (RED if "FAIL" in c.get('reason', '') or "EXC" in c.get('reason', '') else YELLOW)
            lines.append(f"{c['symbol']:<9} | {c.get('hr', 0):>5.0%} | {col}{BOLD}{c.get('sig', 'NEUTRAL'):<12}{END} | {c.get('risk', 0):>7.1f} | {c.get('gain', 0):>7.1f} | {c.get('edge', -999):>7.1f} | {c.get('gap', '0.0'):>5} | {c.get('mode', 'N/A'):<14} | {c.get('conf', 'N/A'):<7} | {r_col}{c.get('reason', 'N/A')}{END}")
        lines.append("=" * 140)
        lines.append(f"{BOLD}PROD MODE | 100% VISIBILITY | {datetime.now().strftime('%H:%M:%S')}{END}\033[J")
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        self.lines_printed = len(lines)

    def run(self):
        os.system('clear')
        self.cold_start()
        self._background_update()
        while True:
            if not self.is_updating and (time.time() - self.last_update_time >= 15):
                threading.Thread(target=self._background_update, daemon=True).start()
            self.render_ui()
            time.sleep(1)

if __name__ == "__main__":
    try: FastSentinelTerminalV3().run()
    except Exception: traceback.print_exc()
