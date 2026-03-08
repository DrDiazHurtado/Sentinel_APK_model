import numpy as np
import pandas as pd
from typing import List, Tuple, Set

class ConformalEngine:
    """
    Cuantificador de incertidumbre mediante Inductive Conformal Prediction (ICP).
    Reforzado para política de NO-TRADE en caso de ambigüedad.
    """
    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.q_hat = None

    def calibrate(self, y_val: np.ndarray, probs_val: np.ndarray):
        n = len(y_val)
        if n < 10: return
        
        scores = []
        for i in range(n):
            correct_prob = probs_val[i, int(y_val[i])]
            scores.append(1 - correct_prob)
        
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        self.q_hat = np.quantile(scores, min(q_level, 1.0))

    def get_prediction_set(self, prob_up: float) -> Set[str]:
        """
        Retorna el set de predicción. 
        Política estricta: Solo sets unitarios {"UP"} o {"DOWN"} son operables.
        """
        if self.q_hat is None:
            return set()
            
        p_up = prob_up
        p_down = 1 - prob_up
        
        prediction_set = set()
        if (1 - p_up) <= self.q_hat:
            prediction_set.add("UP")
        if (1 - p_down) <= self.q_hat:
            prediction_set.add("DOWN")
            
        return prediction_set

    def is_operable(self, prediction_set: Set[str]) -> bool:
        """
        Condición de auditoría: singleton exacto.
        """
        return len(prediction_set) == 1
