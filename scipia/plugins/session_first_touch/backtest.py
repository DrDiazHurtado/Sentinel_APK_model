import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

class Backtest:
    """
    Evaluación de eficacia mediante Walk-Forward (Entrenar en Pasado -> Predecir Futuro).
    """
    def __init__(self, train_ratio=0.7):
        self.train_ratio = train_ratio

    def run_evaluation(self, df, model_engine, feature_cols, label_col):
        """
        Ejecuta la validación y retorna métricas de acierto.
        """
        # Eliminar filas sin etiquetas (donde no se tocó ningún nivel en el horizonte)
        valid_df = df.dropna(subset=[label_col])
        
        if len(valid_df) < 50:
            return {"error": "Insuficientes datos etiquetados para validar."}

        # División temporal estricta (no aleatoria para evitar look-ahead bias)
        split_idx = int(len(valid_df) * self.train_ratio)
        train_df = valid_df.iloc[:split_idx]
        test_df = valid_df.iloc[split_idx:]

        X_train = train_df[feature_cols]
        y_train = train_df[label_col].astype(int)
        
        X_test = test_df[feature_cols]
        y_test = test_df[label_col].astype(int)

        # 1. Entrenamiento
        model_engine.train(X_train, y_train)

        # 2. Predicción
        probs = model_engine.predict_proba(X_test)[:, 1]
        preds = (probs >= 0.5).astype(int)

        # 3. Métricas
        hit_rate = accuracy_score(y_test, preds)
        brier = brier_score_loss(y_test, probs)
        
        try:
            auc = roc_auc_score(y_test, probs)
        except:
            auc = 0.5

        return {
            "test_start": test_df.index[0],
            "test_end": test_df.index[-1],
            "samples": len(test_df),
            "hit_rate": hit_rate,
            "brier_score": brier,
            "auc": auc,
            "expectancy": (hit_rate * 2) - 1 # Simplificado: (W*R - L)
        }
