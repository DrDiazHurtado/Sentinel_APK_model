from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
import joblib
import os

class ModelEngine:
    def __init__(self, model_type: str = "logistic"):
        self.model_type = model_type
        self.model = None

    def train(self, X, y):
        if self.model_type == "logistic":
            base = LogisticRegression(penalty="l2", max_iter=1000)
        else:
            base = GradientBoostingClassifier()
            
        self.model = CalibratedClassifierCV(base, method="sigmoid", cv=5)
        self.model.fit(X, y)
        
    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def save(self, path: str):
        joblib.dump(self.model, path)
        
    def load(self, path: str):
        self.model = joblib.load(path)
