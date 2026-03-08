import numpy as np

class HazardModel:
    """
    Modelo de riesgos competitivos para el 'First Touch'.
    """
    def __init__(self, model_up, model_down):
        self.model_up = model_up
        self.model_down = model_down

    def predict_first_touch_probs(self, X):
        """
        Calcula P(up_first) y P(down_first).
        """
        # Predicción de intensidades (lambda)
        lambda_up = self.model_up.predict_proba(X)[:, 1]
        lambda_down = self.model_down.predict_proba(X)[:, 1]
        
        # Probabilidad relativa bajo riesgo competitivo
        total_intensity = lambda_up + lambda_down
        
        # Evitar división por cero
        total_intensity[total_intensity == 0] = 1.0
        
        p_up = lambda_up / total_intensity
        p_down = lambda_down / total_intensity
        
        return p_up, p_down
