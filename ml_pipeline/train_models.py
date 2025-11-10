"""
Main Training Script for Revenue Prediction Models
Trains all models, compares performance, and saves the best one
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from data_preprocessing import prepare_data
from models import (
    RandomForestModel, XGBoostModel, LightGBMModel, GradientBoostingModel,
    EnsembleModel, ModelEvaluator, save_model, save_results
)


def plot_predictions(y_true, y_pred, model_name, output_path):
    """Plot actual vs predicted values"""
    # Convert from log scale to original
    y_true_orig = np.expm1(y_true)
    y_pred_orig = np.expm1(y_pred)

    plt.figure(figsize=(10, 6))
    plt.scatter(y_true_orig, y_pred_orig, alpha=0.5)
    plt.plot([y_true_orig.min(), y_true_orig.max()],
             [y_true_orig.min(), y_true_orig.max()], 'r--', lw=2)
    plt.xlabel('Actual Revenue ($M)')
    plt.ylabel('Predicted Revenue ($M)')
    plt.title(f'{model_name}: Actual vs Predicted Revenue')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Plot saved to {output_path}")


def plot_feature_importance(feature_importance_df, model_name, output_path, top_n=20):
    """Plot feature importance"""
    plt.figure(figsize=(10, 8))
    top_features = feature_importance_df.head(top_n)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance')
    plt.title(f'{model_name}: Top {top_n} Feature Importances')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Feature importance plot saved to {output_path}")


def plot_residuals(y_true, y_pred, model_name, output_path):
    """Plot residuals"""
    # Convert from log scale
    y_true_orig = np.expm1(y_true)
    y_pred_orig = np.expm1(y_pred)
    residuals = y_true_orig - y_pred_orig

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Residual plot
    axes[0].scatter(y_pred_orig, residuals, alpha=0.5)
    axes[0].axhline(y=0, color='r', linestyle='--')
    axes[0].set_xlabel('Predicted Revenue ($M)')
    axes[0].set_ylabel('Residuals ($M)')
    axes[0].set_title(f'{model_name}: Residual Plot')

    # Residual distribution
    axes[1].hist(residuals, bins=50, edgecolor='black')
    axes[1].set_xlabel('Residuals ($M)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title(f'{model_name}: Residual Distribution')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Residual plot saved to {output_path}")


def plot_model_comparison(results_dict, output_path):
    """Compare all models"""
    metrics = ['r2_original_scale', 'rmse_millions', 'mae_millions', 'mape', 'within_30_percent']
    model_names = list(results_dict.keys())

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for idx, metric in enumerate(metrics):
        values = [results_dict[model][metric] for model in model_names]
        axes[idx].bar(model_names, values, color='skyblue', edgecolor='black')
        axes[idx].set_title(metric.replace('_', ' ').title())
        axes[idx].tick_params(axis='x', rotation=45)
        axes[idx].grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, v in enumerate(values):
            axes[idx].text(i, v, f'{v:.2f}', ha='center', va='bottom')

    # Hide the last subplot if odd number of metrics
    if len(metrics) < len(axes):
        axes[-1].axis('off')

    plt.suptitle('Model Performance Comparison', fontsize=16, y=1.00)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Model comparison plot saved to {output_path}")


def main():
    print("="*80)
    print("REVENUE PREDICTION MODEL TRAINING")
    print("="*80)

    # Create output directories
    output_dir = Path('ml_pipeline/output')
    models_dir = output_dir / 'models'
    plots_dir = output_dir / 'plots'
    results_dir = output_dir / 'results'

    for directory in [models_dir, plots_dir, results_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Step 1: Load and prepare data
    print("\n" + "="*80)
    print("STEP 1: DATA PREPARATION")
    print("="*80)
    data = prepare_data('ml_features_combined_cleaned.csv', test_size=0.2, random_state=42)

    X_train = data['X_train']
    X_test = data['X_test']
    y_train = data['y_train']
    y_test = data['y_test']
    feature_engineer = data['feature_engineer']

    # Save feature engineer
    feature_engineer.save(str(models_dir / 'feature_engineer.pkl'))

    # Step 2: Train Random Forest
    print("\n" + "="*80)
    print("STEP 2: TRAINING RANDOM FOREST")
    print("="*80)
    rf_model = RandomForestModel(
        n_estimators=300,
        max_depth=25,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    rf_model.train(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    rf_metrics = ModelEvaluator.evaluate_model(y_test, rf_pred, "Random Forest")

    # Save Random Forest
    save_model(rf_model, str(models_dir / 'random_forest.pkl'))
    plot_predictions(y_test, rf_pred, "Random Forest", str(plots_dir / 'rf_predictions.png'))
    plot_feature_importance(rf_model.feature_importance, "Random Forest",
                          str(plots_dir / 'rf_feature_importance.png'))
    plot_residuals(y_test, rf_pred, "Random Forest", str(plots_dir / 'rf_residuals.png'))

    # Step 3: Train XGBoost
    print("\n" + "="*80)
    print("STEP 3: TRAINING XGBOOST")
    print("="*80)

    xgb_model = XGBoostModel(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    xgb_model.train(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)
    xgb_metrics = ModelEvaluator.evaluate_model(y_test, xgb_pred, "XGBoost")

    # Save XGBoost
    save_model(xgb_model, str(models_dir / 'xgboost.pkl'))
    plot_predictions(y_test, xgb_pred, "XGBoost", str(plots_dir / 'xgb_predictions.png'))
    plot_feature_importance(xgb_model.feature_importance, "XGBoost",
                          str(plots_dir / 'xgb_feature_importance.png'))
    plot_residuals(y_test, xgb_pred, "XGBoost", str(plots_dir / 'xgb_residuals.png'))

    # Step 4: Train LightGBM
    print("\n" + "="*80)
    print("STEP 4: TRAINING LIGHTGBM")
    print("="*80)
    lgb_model = LightGBMModel(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.05,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    lgb_model.train(X_train, y_train)
    lgb_pred = lgb_model.predict(X_test)
    lgb_metrics = ModelEvaluator.evaluate_model(y_test, lgb_pred, "LightGBM")

    # Save LightGBM
    save_model(lgb_model, str(models_dir / 'lightgbm.pkl'))
    plot_predictions(y_test, lgb_pred, "LightGBM", str(plots_dir / 'lgb_predictions.png'))
    plot_feature_importance(lgb_model.feature_importance, "LightGBM",
                          str(plots_dir / 'lgb_feature_importance.png'))
    plot_residuals(y_test, lgb_pred, "LightGBM", str(plots_dir / 'lgb_residuals.png'))

    # Step 5: Create Ensemble
    print("\n" + "="*80)
    print("STEP 5: CREATING ENSEMBLE MODEL")
    print("="*80)

    # Create ensemble with top 3 models (equal weights)
    ensemble = EnsembleModel([rf_model, xgb_model, lgb_model])

    # Use equal weights
    ensemble.optimize_weights(None, None, method='equal')

    # Evaluate ensemble
    ensemble_pred = ensemble.predict(X_test)
    ensemble_metrics = ModelEvaluator.evaluate_model(y_test, ensemble_pred, "Ensemble")

    # Save ensemble
    save_model(ensemble, str(models_dir / 'ensemble.pkl'))
    plot_predictions(y_test, ensemble_pred, "Ensemble", str(plots_dir / 'ensemble_predictions.png'))
    plot_residuals(y_test, ensemble_pred, "Ensemble", str(plots_dir / 'ensemble_residuals.png'))

    # Step 6: Compare all models
    print("\n" + "="*80)
    print("STEP 6: MODEL COMPARISON")
    print("="*80)

    all_metrics = {
        'Random Forest': rf_metrics,
        'XGBoost': xgb_metrics,
        'LightGBM': lgb_metrics,
        'Ensemble': ensemble_metrics
    }

    # Create comparison table
    comparison_df = pd.DataFrame(all_metrics).T
    print("\n" + comparison_df.to_string())

    # Save comparison
    comparison_df.to_csv(str(results_dir / 'model_comparison.csv'))
    plot_model_comparison(all_metrics, str(plots_dir / 'model_comparison.png'))

    # Determine best model
    best_model_name = comparison_df['r2_original_scale'].idxmax()
    print(f"\n{'='*80}")
    print(f"BEST MODEL: {best_model_name}")
    print(f"R² Score: {comparison_df.loc[best_model_name, 'r2_original_scale']:.4f}")
    print(f"{'='*80}")

    # Save comprehensive results
    final_results = {
        'metrics': all_metrics,
        'best_model': best_model_name,
        'feature_names': data['feature_names'],
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'ensemble_weights': {
            'Random Forest': ensemble.weights[0],
            'XGBoost': ensemble.weights[1],
            'LightGBM': ensemble.weights[2]
        }
    }

    save_results(final_results, str(results_dir / 'training_results.json'))

    # Feature importance comparison (top 20 features across models)
    print("\n" + "="*80)
    print("TOP 20 FEATURES (BY AVERAGE IMPORTANCE)")
    print("="*80)

    # Combine feature importances
    all_importances = pd.DataFrame({
        'RF': rf_model.feature_importance.set_index('feature')['importance'],
        'XGB': xgb_model.feature_importance.set_index('feature')['importance'],
        'LGB': lgb_model.feature_importance.set_index('feature')['importance']
    })
    all_importances['Average'] = all_importances.mean(axis=1)
    all_importances = all_importances.sort_values('Average', ascending=False)

    print(all_importances.head(20).to_string())
    all_importances.to_csv(str(results_dir / 'feature_importance_comparison.csv'))

    # Plot combined feature importance
    plt.figure(figsize=(12, 8))
    top_20 = all_importances.head(20)
    x = np.arange(len(top_20))
    width = 0.25

    plt.barh(x - width, top_20['RF'], width, label='Random Forest')
    plt.barh(x, top_20['XGB'], width, label='XGBoost')
    plt.barh(x + width, top_20['LGB'], width, label='LightGBM')

    plt.yticks(x, top_20.index)
    plt.xlabel('Importance')
    plt.title('Feature Importance Comparison - Top 20 Features')
    plt.legend()
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(str(plots_dir / 'feature_importance_comparison.png'), dpi=150)
    plt.close()

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"Models saved to: {models_dir}")
    print(f"Plots saved to: {plots_dir}")
    print(f"Results saved to: {results_dir}")


if __name__ == "__main__":
    main()
