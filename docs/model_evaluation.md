# SmartKhet 2.0: Model Evaluation, Verification & Diagnostics

## 1. Empirical Test Set Results (Unseen Chronological Split: N=822)

All metrics below are computed on the chronological holdout test set (April 1, 2023 to December 30, 2023):

| Metric | Baseline (Persistence) | Random Forest (Deployed) | XGBoost Regressor |
|---|---|---|---|
| **Mean Absolute Error (MAE)** | $0.0044\text{ m}^3/\text{m}^3$ | **$0.0040\text{ m}^3/\text{m}^3$** | $0.0042\text{ m}^3/\text{m}^3$ |
| **Root Mean Squared Error (RMSE)** | $0.0103\text{ m}^3/\text{m}^3$ | **$0.0082\text{ m}^3/\text{m}^3$** | $0.0086\text{ m}^3/\text{m}^3$ |
| **Coefficient of Determination ($R^2$)** | $0.7946$ | **$0.8722$** | $0.8582$ |
| **Median Absolute Error (MedAE)** | $0.0000\text{ m}^3/\text{m}^3$ | **$0.0012\text{ m}^3/\text{m}^3$** | $0.0013\text{ m}^3/\text{m}^3$ |
| **Edge Inference Latency** | $0\text{ ms}$ | **$12.4\text{ ms}$** | $14.1\text{ ms}$ |

---

## 2. Metric Formulations & Interpretation

### 2.1 Coefficient of Determination ($R^2$)
$$R^2 = 1 - \frac{\sum_{i=1}^n (y_i - \hat{y}_i)^2}{\sum_{i=1}^n (y_i - \bar{y})^2}$$
- **Interpretation:** The Random Forest model explains **$87.22\%$** of the total variance in next-day soil moisture.
- **Academic Rule:** $R^2$ is a variance ratio, **never** to be described as an "accuracy percentage".

### 2.2 Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2} = 0.0082\text{ m}^3/\text{m}^3$$
- Penalizes large outlier errors, providing confidence that sudden rainfall events or severe dry-downs are captured without catastrophic mispredictions.

### 2.3 Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i| = 0.0040\text{ m}^3/\text{m}^3$$
- On average, the model's prediction deviates from ground truth by only $0.004$ volumetric units (~$0.4\%$ moisture content), well within the agronomic safety margin ($1.5\%$).

---

## 3. Feature Importance & Explainability (MDI)

Mean Decrease in Impurity demonstrates that:
1. `soil_moisture_lag1` ($48.5\%$): Strongest single predictor (hydrological inertia).
2. `soil_moisture_ma3` ($21.4\%$): Short-term memory.
3. `soil_moisture_ma7` ($12.1\%$): Subsoil root-zone reserve.
4. `rainfall_mm` ($6.5\%$): Rapid replenishment trigger.
5. Meteorological variables ($11.5\%$ combined): Evaporative loss drivers.

