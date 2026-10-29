"""
Shared compatibility module for TwoStageModel.
This module is accessible from both training scripts and backend services.
"""

import numpy as np
from typing import Optional
from sklearn.base import BaseEstimator


class TwoStageModel:
    """Two-stage model for zero-inflated targets.
    
    Stage 1: Binary classifier (zero vs non-zero)
    Stage 2: Regressor for non-zero values
    """
    
    def __init__(self, classifier=None, regressor=None):
        self.classifier = classifier
        self.regressor = regressor
        self.is_fitted = False
        self.mean_non_zero = 0.0
    
    def fit(self, X, y):
        y_binary = (y > 0).astype(int)
        self.classifier.fit(X, y_binary)
        non_zero_mask = y > 0
        if non_zero_mask.sum() > 10:
            self.regressor.fit(X[non_zero_mask], y[non_zero_mask])
        else:
            self.mean_non_zero = y[non_zero_mask].mean() if non_zero_mask.any() else 0
        self.is_fitted = True
        return self
    
    def predict(self, X):
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        prob_non_zero = self.classifier.predict_proba(X)[:, 1]
        if hasattr(self, 'regressor') and hasattr(self.regressor, 'predict'):
            y_pred_reg = self.regressor.predict(X)
        else:
            y_pred_reg = np.full(len(X), self.mean_non_zero)
        y_pred = np.where(prob_non_zero > 0.5, y_pred_reg, 0)
        return np.maximum(y_pred, 0)
    
    def predict_proba(self, X):
        return self.classifier.predict_proba(X)

    def __getstate__(self):
        return self.__dict__
    
    def __setstate__(self, state):
        self.__dict__.update(state)