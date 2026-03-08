import torch
import torch.nn as nn
import numpy as np

class KANLayer(nn.Module):
    """
    Capa KAN simplificada para el plugin.
    Aprende funciones no lineales sobre los inputs.
    """
    def __init__(self, in_features, out_features):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        # Usamos una combinación de pesos lineales y no lineales (sinusoidales)
        self.lineal = nn.Linear(in_features, out_features)
        self.nonlinear = nn.Parameter(torch.randn(in_features, out_features))

    def forward(self, x):
        # x: [batch, in_features]
        # Parte lineal + Parte no lineal (sinusoidal)
        res = self.lineal(x)
        # Aplicamos la base KAN (simplificada a sin(x))
        non_lin = torch.mm(torch.sin(x), self.nonlinear)
        return torch.tanh(res + non_lin)

class KANModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.layer1 = KANLayer(input_dim, 16)
        self.layer2 = KANLayer(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        return self.sigmoid(x)

class KANModelEngine:
    def __init__(self, input_dim):
        self.model = KANModel(input_dim)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.criterion = nn.BCELoss()

    def train(self, X, y, epochs=50):
        # Asegurar tipos correctos
        X_t = torch.FloatTensor(X.values if hasattr(X, 'values') else X)
        y_t = torch.FloatTensor(y.values if hasattr(y, 'values') else y).view(-1, 1)
        
        self.model.train()
        for _ in range(epochs):
            self.optimizer.zero_grad()
            output = self.model(X_t)
            loss = self.criterion(output, y_t)
            loss.backward()
            self.optimizer.step()

    def predict_proba(self, X):
        X_t = torch.FloatTensor(X.values if hasattr(X, 'values') else X)
        self.model.eval()
        with torch.no_grad():
            prob_up = self.model(X_t).numpy().flatten()
        return np.stack([1 - prob_up, prob_up], axis=1)
