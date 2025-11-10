"""
Machine Learning Models for Revenue Prediction
Includes Random Forest, XGBoost, LightGBM, Neural Network, and Ensemble
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import cross_val_score, KFold
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, Any, List, Tuple
import pickle
import json
from pathlib import Path
import time


class ModelEvaluator:
    """Evaluate and compare models"""

    @staticmethod
    def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, model_name: str = "") -> Dict[str, float]:
        """
        Comprehensive model evaluation metrics
        Assumes y_true and y_pred are log-transformed
        """
        # Convert back to original scale for meaningful metrics
        y_true_orig = np.expm1(y_true)
        y_pred_orig = np.expm1(y_pred)

        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'rmse_millions': np.sqrt(mean_squared_error(y_true_orig, y_pred_orig)),
            'mae': mean_absolute_error(y_true, y_pred),
            'mae_millions': mean_absolute_error(y_true_orig, y_pred_orig),
            'r2': r2_score(y_true, y_pred),
            'r2_original_scale': r2_score(y_true_orig, y_pred_orig),
            'mape': mean_absolute_percentage_error(y_true_orig, y_pred_orig) * 100,
        }

        # Custom metric: percentage of predictions within X% of actual
        errors = np.abs(y_pred_orig - y_true_orig) / (y_true_orig + 1)
        metrics['within_20_percent'] = (errors <= 0.20).mean() * 100
        metrics['within_30_percent'] = (errors <= 0.30).mean() * 100
        metrics['within_50_percent'] = (errors <= 0.50).mean() * 100

        if model_name:
            print(f"\n{'='*80}")
            print(f"{model_name} PERFORMANCE")
            print(f"{'='*80}")
            print(f"R² Score (log scale):        {metrics['r2']:.4f}")
            print(f"R² Score (original scale):   {metrics['r2_original_scale']:.4f}")
            print(f"RMSE (log scale):            {metrics['rmse']:.4f}")
            print(f"RMSE (millions $):           ${metrics['rmse_millions']:.2f}M")
            print(f"MAE (millions $):            ${metrics['mae_millions']:.2f}M")
            print(f"MAPE:                        {metrics['mape']:.2f}%")
            print(f"Within 20% accuracy:         {metrics['within_20_percent']:.1f}%")
            print(f"Within 30% accuracy:         {metrics['within_30_percent']:.1f}%")
            print(f"Within 50% accuracy:         {metrics['within_50_percent']:.1f}%")

        return metrics


class RandomForestModel:
    """Random Forest with hyperparameter tuning"""

    def __init__(self, n_estimators: int = 200, max_depth: int = 20,
                 min_samples_split: int = 5, min_samples_leaf: int = 2,
                 max_features: str = 'sqrt', random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            random_state=random_state,
            n_jobs=-1
        )
        self.feature_importance = None
        self.training_time = 0

    def train(self, X_train: pd.DataFrame, y_train: np.ndarray) -> 'RandomForestModel':
        """Train the model"""
        print("\nTraining Random Forest...")
        start_time = time.time()
        self.model.fit(X_train, y_train)
        self.training_time = time.time() - start_time
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(f"Training completed in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)

    def cross_validate(self, X: pd.DataFrame, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation"""
        print(f"\nPerforming {cv}-fold cross-validation...")
        scores = cross_val_score(self.model, X, y, cv=cv, scoring='r2', n_jobs=-1)
        return {
            'cv_r2_mean': scores.mean(),
            'cv_r2_std': scores.std()
        }


class XGBoostModel:
    """XGBoost with hyperparameter tuning"""

    def __init__(self, n_estimators: int = 200, max_depth: int = 8,
                 learning_rate: float = 0.1, subsample: float = 0.8,
                 colsample_bytree: float = 0.8, random_state: int = 42):
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1,
            tree_method='hist'
        )
        self.feature_importance = None
        self.training_time = 0

    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
              X_val: pd.DataFrame = None, y_val: np.ndarray = None,
              early_stopping_rounds: int = 50) -> 'XGBoostModel':
        """Train the model with optional early stopping"""
        print("\nTraining XGBoost...")
        start_time = time.time()

        # Simple training without early stopping for compatibility
        self.model.fit(X_train, y_train)

        self.training_time = time.time() - start_time
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(f"Training completed in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)

    def cross_validate(self, X: pd.DataFrame, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation"""
        print(f"\nPerforming {cv}-fold cross-validation...")
        scores = cross_val_score(self.model, X, y, cv=cv, scoring='r2', n_jobs=-1)
        return {
            'cv_r2_mean': scores.mean(),
            'cv_r2_std': scores.std()
        }


class LightGBMModel:
    """LightGBM with hyperparameter tuning"""

    def __init__(self, n_estimators: int = 200, max_depth: int = 8,
                 learning_rate: float = 0.1, num_leaves: int = 31,
                 subsample: float = 0.8, colsample_bytree: float = 0.8,
                 random_state: int = 42):
        self.model = lgb.LGBMRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1,
            verbose=-1
        )
        self.feature_importance = None
        self.training_time = 0

    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
              X_val: pd.DataFrame = None, y_val: np.ndarray = None,
              early_stopping_rounds: int = 50) -> 'LightGBMModel':
        """Train the model with optional early stopping"""
        print("\nTraining LightGBM...")
        start_time = time.time()

        # Simple training for compatibility
        self.model.fit(X_train, y_train)

        self.training_time = time.time() - start_time
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(f"Training completed in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)

    def cross_validate(self, X: pd.DataFrame, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
        """Perform cross-validation"""
        print(f"\nPerforming {cv}-fold cross-validation...")
        scores = cross_val_score(self.model, X, y, cv=cv, scoring='r2', n_jobs=-1)
        return {
            'cv_r2_mean': scores.mean(),
            'cv_r2_std': scores.std()
        }


class GradientBoostingModel:
    """Gradient Boosting as additional ensemble member"""

    def __init__(self, n_estimators: int = 200, max_depth: int = 8,
                 learning_rate: float = 0.1, subsample: float = 0.8,
                 random_state: int = 42):
        from sklearn.ensemble import HistGradientBoostingRegressor
        self.model = HistGradientBoostingRegressor(
            max_iter=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state
        )
        self.feature_importance = None
        self.training_time = 0

    def train(self, X_train: pd.DataFrame, y_train: np.ndarray) -> 'GradientBoostingModel':
        """Train the model"""
        print("\nTraining Gradient Boosting...")
        start_time = time.time()
        self.model.fit(X_train, y_train)
        self.training_time = time.time() - start_time
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(f"Training completed in {self.training_time:.2f} seconds")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)


class EnsembleModel:
    """Weighted ensemble of multiple models"""

    def __init__(self, models: List[Any], weights: List[float] = None):
        """
        Initialize ensemble

        Args:
            models: List of trained models
            weights: Optional weights for each model (will be normalized)
        """
        self.models = models
        if weights is None:
            weights = [1.0 / len(models)] * len(models)
        else:
            # Normalize weights
            total = sum(weights)
            weights = [w / total for w in weights]
        self.weights = weights

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make weighted ensemble predictions"""
        predictions = np.zeros(len(X))
        for model, weight in zip(self.models, self.weights):
            predictions += weight * model.predict(X)
        return predictions

    def optimize_weights(self, X_val: pd.DataFrame, y_val: np.ndarray,
                        method: str = 'grid') -> List[float]:
        """
        Optimize ensemble weights based on validation performance

        Args:
            X_val: Validation features
            y_val: Validation target
            method: 'grid' for grid search, 'equal' for equal weights
        """
        if method == 'equal':
            self.weights = [1.0 / len(self.models)] * len(self.models)
            return self.weights

        # Grid search for optimal weights
        print("\nOptimizing ensemble weights...")
        best_score = float('inf')
        best_weights = None

        # Try different weight combinations
        from itertools import product
        weight_options = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

        for weights in product(weight_options, repeat=len(self.models)):
            if sum(weights) == 0:
                continue

            # Normalize
            normalized = [w / sum(weights) for w in weights]

            # Calculate predictions
            predictions = np.zeros(len(X_val))
            for model, weight in zip(self.models, normalized):
                predictions += weight * model.predict(X_val)

            # Calculate error
            mse = mean_squared_error(y_val, predictions)

            if mse < best_score:
                best_score = mse
                best_weights = normalized

        self.weights = best_weights
        print(f"Optimal weights: {[f'{w:.2f}' for w in self.weights]}")
        return self.weights


def save_model(model: Any, filepath: str):
    """Save a trained model"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {filepath}")


def load_model(filepath: str) -> Any:
    """Load a saved model"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def save_results(results: Dict[str, Any], filepath: str):
    """Save model results and metrics"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        return obj

    serializable_results = convert_to_serializable(results)

    with open(filepath, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    print(f"Results saved to {filepath}")
