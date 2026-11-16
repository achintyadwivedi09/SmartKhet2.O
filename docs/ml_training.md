# SmartKhet 2.0: Machine Learning Methodology & Training Strategy

## 1. Problem Formulation

The core machine learning task is formulated as a single-step ahead autoregressive regression problem:
$$\hat{\theta}_{t+1} = f(\boldsymbol{x}_t)$$

Where:
- $\hat{\theta}_{t+1}$ is the predicted next-day volumetric soil moisture ($\text{m}^3/\text{m}^3$).
- $\boldsymbol{x}_t \in \mathbb{R}^{16}$ is the input feature vector available at prediction time $t$.

---

## 2. Model Architectures

### 2.1 Model A: Random Forest Regressor (Primary Deployed)
- **Algorithm:** Bagging ensemble of $B=200$ de-correlated regression decision trees.
- **Hyperparameters:**
  - `n_estimators`: 200
  - `max_depth`: 14
  - `min_samples_split`: 5
  - `min_samples_leaf`: 2
  - `random_state`: 42
  - `criterion`: squared_error
- **Selection Rationale:**
  - Highly robust to non-linear relationships and collinearity among meteorological lags.
  - Immune to feature scaling issues.
  - Exceptionally fast inference time on resource-constrained edge Fog nodes (~$12\text{ ms}$).

### 2.2 Model B: XGBoost Regressor (Benchmark)
- **Algorithm:** Extreme Gradient Boosted Trees optimizing second-order Taylor expansion loss.
- **Hyperparameters:**
  - `n_estimators`: 250
  - `max_depth`: 6
  - `learning_rate`: 0.05
  - `subsample`: 0.85
  - `colsample_bytree`: 0.85
  - `random_state`: 42

### 2.3 Model C: Persistence Baseline
- **Formula:** $\hat{\theta}_{t+1} = \theta_t$
- **Purpose:** Minimum scientific standard for time-series forecasting. Any ML model must decisively outperform persistence to justify operational deployment.

---

## 3. Strict Chronological Splitting Strategy

Standard random k-fold cross-validation or random `train_test_split` causes severe data leakage in time-series problems by mixing future correlations into past predictions.

SmartKhet 2.0 uses chronological splitting:
1. **Training Set ($70\%$):** 2019-01-01 to 2022-07-01 ($3,832$ samples).
2. **Validation Set ($15\%$):** 2022-07-01 to 2023-03-31 ($821$ samples).
3. **Test Set ($15\%$):** 2023-04-01 to 2023-12-30 ($822$ samples).

