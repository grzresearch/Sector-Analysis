"""
Regression & Forecasting Models
OLS regression and machine learning models for stock performance prediction
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Statistical models
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Machine learning models
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


# =============================================================================
# OLS REGRESSION ANALYSIS
# =============================================================================

def prepare_regression_data(df, target='excess_return', features=None):
    """
    Prepare data for regression analysis
    """
    if features is None:
        features = [
            'forward_pe', 'price_to_book', 'debt_to_equity', 'roe',
            'profit_margin', 'revenue_growth', 'volatility', 'beta'
        ]

    # Select available features
    available_features = [f for f in features if f in df.columns]

    # Create regression dataset
    reg_data = df[[target] + available_features].copy()
    reg_data = reg_data.replace([np.inf, -np.inf], np.nan)
    reg_data = reg_data.dropna()

    return reg_data, available_features


def run_ols_regression(df, target='excess_return', features=None, add_constant=True):
    """
    Run OLS regression to analyze factors affecting stock performance

    Returns:
    - model: fitted OLS model
    - summary: regression summary
    - predictions: predicted values
    - residuals: residuals
    """
    reg_data, available_features = prepare_regression_data(df, target, features)

    if len(reg_data) < 30:
        print(f"Warning: Only {len(reg_data)} observations available for regression")
        if len(reg_data) < 10:
            return None, None, None, None

    X = reg_data[available_features]
    y = reg_data[target]

    if add_constant:
        X = sm.add_constant(X)

    model = OLS(y, X).fit()
    predictions = model.predict(X)
    residuals = y - predictions

    return model, model.summary(), predictions, residuals


def run_sector_ols(df, target='1y_return'):
    """
    Run OLS regression for each sector separately
    Returns dict of {sector: model}
    """
    sector_models = {}

    for sector in df['sector'].unique():
        sector_df = df[df['sector'] == sector]

        if len(sector_df) < 20:
            continue

        model, summary, _, _ = run_ols_regression(sector_df, target)

        if model is not None:
            sector_models[sector] = {
                'model': model,
                'r2': model.rsquared,
                'adj_r2': model.rsquared_adj,
                'n_obs': model.nobs,
                'significant_factors': [
                    (name, coef, pval)
                    for name, coef, pval in zip(model.params.index, model.params, model.pvalues)
                    if pval < 0.05 and name != 'const'
                ]
            }

    return sector_models


def calculate_vif(df, features):
    """Calculate Variance Inflation Factor for multicollinearity check"""
    X = df[features].dropna()

    if len(X) < len(features) + 1:
        return None

    vif_data = pd.DataFrame()
    vif_data['feature'] = features
    vif_data['VIF'] = [
        variance_inflation_factor(X.values, i)
        for i in range(len(features))
    ]

    return vif_data


def analyze_regression_results(model):
    """Analyze and interpret OLS regression results"""
    results = {
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'f_statistic': model.fvalue,
        'f_pvalue': model.f_pvalue,
        'aic': model.aic,
        'bic': model.bic,
        'n_observations': model.nobs,
    }

    # Significant coefficients
    sig_coefs = []
    for name, coef, se, pval in zip(model.params.index, model.params,
                                      model.bse, model.pvalues):
        if pval < 0.1:  # 10% significance level
            sig_coefs.append({
                'factor': name,
                'coefficient': coef,
                'std_error': se,
                'p_value': pval,
                'significance': '***' if pval < 0.01 else '**' if pval < 0.05 else '*'
            })

    results['significant_factors'] = sig_coefs

    # Interpretation
    interpretations = []
    for factor in sig_coefs:
        if factor['factor'] == 'const':
            continue
        direction = 'positive' if factor['coefficient'] > 0 else 'negative'
        interpretations.append(
            f"{factor['factor']}: {direction} effect on returns "
            f"(β={factor['coefficient']:.4f}, p={factor['p_value']:.4f})"
        )

    results['interpretations'] = interpretations

    return results


# =============================================================================
# MACHINE LEARNING MODELS
# =============================================================================

def train_ml_models(df, target='1y_return', features=None, test_size=0.2):
    """
    Train multiple ML models for stock return prediction

    Returns:
    - models: dict of fitted models
    - performance: dict of model performance metrics
    - predictions: predictions on test set
    """
    reg_data, available_features = prepare_regression_data(df, target, features)

    if len(reg_data) < 50:
        print(f"Warning: Only {len(reg_data)} samples available for ML")
        if len(reg_data) < 30:
            return None, None, None

    X = reg_data[available_features]
    y = reg_data[target]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Define models
    models = {
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.01),
        'ElasticNet': ElasticNet(alpha=0.01, l1_ratio=0.5),
        'RandomForest': RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
    }

    results = {}
    predictions = {}

    for name, model in models.items():
        try:
            # Use scaled data for linear models, raw for tree-based
            if name in ['Ridge', 'Lasso', 'ElasticNet']:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                cv_scores = cross_val_score(
                    model, X_train_scaled, y_train, cv=5, scoring='r2'
                )
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring='r2'
                )

            results[name] = {
                'model': model,
                'r2': r2_score(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'mae': mean_absolute_error(y_test, y_pred),
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std()
            }
            predictions[name] = y_pred

        except Exception as e:
            print(f"Error training {name}: {e}")

    return results, predictions, (X_test, y_test, scaler, available_features)


def get_feature_importance(ml_results, feature_names):
    """Extract feature importance from ML models"""
    importance_df = pd.DataFrame(index=feature_names)

    for name, result in ml_results.items():
        model = result['model']

        if hasattr(model, 'feature_importances_'):
            importance_df[name] = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance_df[name] = np.abs(model.coef_)

    importance_df['average'] = importance_df.mean(axis=1)
    importance_df = importance_df.sort_values('average', ascending=False)

    return importance_df


# =============================================================================
# FORECASTING & PREDICTIONS
# =============================================================================

def predict_future_performance(df, model_results, features, scaler=None):
    """
    Generate predictions for stock future performance
    """
    predictions = {}

    # Use the best performing model
    best_model_name = max(model_results.keys(), key=lambda k: model_results[k]['r2'])
    best_model = model_results[best_model_name]['model']

    X = df[features].copy()
    X = X.replace([np.inf, -np.inf], np.nan)

    # Handle missing values
    X = X.fillna(X.median())

    # Scale if necessary
    if scaler is not None and best_model_name in ['Ridge', 'Lasso', 'ElasticNet']:
        X_scaled = scaler.transform(X)
        preds = best_model.predict(X_scaled)
    else:
        preds = best_model.predict(X)

    df_pred = df.copy()
    df_pred['predicted_return'] = preds

    # Classify predictions
    df_pred['return_outlook'] = pd.cut(
        df_pred['predicted_return'],
        bins=[-np.inf, -0.1, -0.02, 0.02, 0.1, np.inf],
        labels=['Strong Decline', 'Decline', 'Neutral', 'Growth', 'Strong Growth']
    )

    return df_pred, best_model_name


def generate_sector_outlook(df, sector_models):
    """
    Generate sector-level outlook based on OLS results
    """
    outlook = {}

    for sector, model_data in sector_models.items():
        model = model_data['model']
        sector_df = df[df['sector'] == sector]

        # Get significant factors
        sig_factors = model_data['significant_factors']

        # Analyze current state vs historical
        outlook[sector] = {
            'r_squared': model_data['r2'],
            'key_drivers': [f[0] for f in sig_factors[:3]],
            'sample_size': model_data['n_obs'],
        }

        # Determine outlook based on current factor values
        if len(sig_factors) > 0:
            # Simple heuristic based on positive/negative factors
            positive_factors = sum(1 for f in sig_factors if f[1] > 0)
            negative_factors = len(sig_factors) - positive_factors

            if positive_factors > negative_factors:
                outlook[sector]['outlook'] = 'Positive'
            elif negative_factors > positive_factors:
                outlook[sector]['outlook'] = 'Negative'
            else:
                outlook[sector]['outlook'] = 'Neutral'
        else:
            outlook[sector]['outlook'] = 'Insufficient Data'

    return outlook


# =============================================================================
# COMPREHENSIVE ANALYSIS REPORT
# =============================================================================

def generate_regression_report(df, output_path=None):
    """
    Generate comprehensive regression analysis report
    """
    report = []
    report.append("=" * 70)
    report.append("REGRESSION ANALYSIS REPORT")
    report.append("Stock Performance Factor Analysis")
    report.append("=" * 70)

    # 1. Overall OLS regression
    report.append("\n1. OVERALL MARKET REGRESSION (OLS)")
    report.append("-" * 50)

    model, summary, preds, residuals = run_ols_regression(df, target='excess_return')

    if model is not None:
        results = analyze_regression_results(model)

        report.append(f"R-squared: {results['r_squared']:.4f}")
        report.append(f"Adjusted R-squared: {results['adj_r_squared']:.4f}")
        report.append(f"F-statistic: {results['f_statistic']:.2f} (p={results['f_pvalue']:.4f})")
        report.append(f"Observations: {results['n_observations']:.0f}")

        report.append("\nSignificant Factors:")
        for factor in results['significant_factors']:
            report.append(f"  {factor['factor']}: β={factor['coefficient']:.4f} "
                         f"(p={factor['p_value']:.4f}) {factor['significance']}")

        report.append("\nInterpretation:")
        for interp in results['interpretations']:
            report.append(f"  • {interp}")

    # 2. Sector-specific regressions
    report.append("\n\n2. SECTOR-SPECIFIC REGRESSIONS")
    report.append("-" * 50)

    sector_models = run_sector_ols(df)

    for sector, data in sorted(sector_models.items(), key=lambda x: -x[1]['r2']):
        report.append(f"\n{sector}:")
        report.append(f"  R²: {data['r2']:.4f} | Adj R²: {data['adj_r2']:.4f} | n={data['n_obs']:.0f}")
        if data['significant_factors']:
            report.append(f"  Key factors: {', '.join([f[0] for f in data['significant_factors'][:3]])}")

    # 3. ML Model Performance
    report.append("\n\n3. MACHINE LEARNING MODELS")
    report.append("-" * 50)

    ml_results, ml_preds, ml_data = train_ml_models(df)

    if ml_results is not None:
        report.append("\nModel Performance (Test Set):")
        for name, metrics in sorted(ml_results.items(), key=lambda x: -x[1]['r2']):
            report.append(f"  {name:20s}: R²={metrics['r2']:.4f} | "
                         f"RMSE={metrics['rmse']:.4f} | CV R²={metrics['cv_r2_mean']:.4f}")

        # Feature importance
        X_test, y_test, scaler, features = ml_data
        importance = get_feature_importance(ml_results, features)

        report.append("\nFeature Importance (Average across models):")
        for feat, imp in importance['average'].head(5).items():
            report.append(f"  {feat:20s}: {imp:.4f}")

    # 4. Sector Outlook
    report.append("\n\n4. SECTOR OUTLOOK")
    report.append("-" * 50)

    outlook = generate_sector_outlook(df, sector_models)

    for sector, data in sorted(outlook.items(), key=lambda x: x[1].get('r_squared', 0), reverse=True):
        report.append(f"\n{sector}:")
        report.append(f"  Outlook: {data.get('outlook', 'N/A')}")
        report.append(f"  Key Drivers: {', '.join(data.get('key_drivers', ['N/A']))}")
        report.append(f"  Model Fit (R²): {data.get('r_squared', 0):.4f}")

    report.append("\n" + "=" * 70)
    report.append("END OF REGRESSION REPORT")
    report.append("=" * 70)

    report_text = "\n".join(report)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(report_text)
        print(f"Regression report saved to {output_path}")

    return report_text, model, sector_models, ml_results
