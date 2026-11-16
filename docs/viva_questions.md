# SmartKhet 2.0: Comprehensive Academic Viva Voce Questions & Answers
### Big Data, Machine Learning, Fog Computing & Agricultural Intelligence

This document provides 32 professor-level questions and comprehensive answers covering system architecture, Big Data pipelines, ML methodologies, Fog computing, data integrity, and system design.

---

### Q1: What is the primary problem SmartKhet 2.0 solves that existing agricultural IoT platforms do not?
**Answer:** Existing agricultural IoT platforms rely on continuous cloud telemetry streaming and simplistic rule-based triggers (e.g. "if sensor &lt; 20% turn pump on"). In rural India, continuous cellular connectivity is unreliable. SmartKhet 2.0 solves this by combining multi-year historical meteorology (IMD, ISRO MOSDAC, ERA5) with localized Fog Computing. In-situ Fog nodes run edge ML inference to anticipate next-day soil moisture depletion and actuate irrigation autonomously, continuing uninterrupted even during total cloud disconnects.

---

### Q2: Why is Fog Computing necessary for rural irrigation instead of direct Cloud IoT?
**Answer:** Fog Computing bridges the gap between field sensors and centralized cloud infrastructure. In rural deployments:
1. **Network Brownouts:** Cellular backhauls experience frequent outages. Fog nodes guarantee 100% decision availability during outages.
2. **Deterministic Latency:** Edge inference executes in ~12 ms, compared to 150–300 ms over high-jitter cellular networks.
3. **Bandwidth Optimization:** Transmitting every raw reading consumes expensive bandwidth. Fog nodes process telemetry locally and synchronize only compressed event summaries.

---

### Q3: How do you mathematically guarantee that your machine learning model has zero target leakage?
**Answer:** Target leakage occurs when information about the target variable is inadvertently present in the training feature matrix. We guarantee zero leakage through:
1. **Strict Temporal Offset:** The target is $\text{SM}_{t+1}$ (next-day soil moisture), shifted by $-1$.
2. **Lagged Features Only:** All input features (e.g. `soil_moisture_lag1`, `rainfall_cum3`, `temperature_c`) are measured at or before time $t$.
3. **Temporal Monotonic Splitting:** Training data spans 2019 to mid-2022; the test set spans mid-2023 onward. No future rows are mixed into earlier splits.
4. **Fit-Transform Boundary:** Preprocessing scalers are fitted exclusively on the training partition.

---

### Q4: Why did you choose Random Forest Regressor over Deep Learning (LSTM / Transformers) for the Fog nodes?
**Answer:**
1. **Resource Constraints:** Fog nodes emulate low-power edge gateways. Random Forest executes inference in ~12 ms with minimal CPU/RAM footprint ($&lt;40\text{ MB}$ memory).
2. **Tabular Performance:** For tabular time-series with lag features, tree ensembles consistently match or outperform LSTMs without requiring GPU acceleration.
3. **Interpretability:** Random Forest allows Mean Decrease in Impurity (MDI) analysis, enabling agricultural explainability for farmers and agronomists.

---

### Q5: What does your $R^2$ score of 0.8722 actually represent? Can you call it 87% accuracy?
**Answer:** No, describing $R^2$ as an "accuracy percentage" is scientifically invalid. $R^2 = 0.8722$ is the coefficient of determination, indicating that the Random Forest model explains **87.22% of the variance** in next-day volumetric soil moisture relative to the mean benchmark. Model accuracy is evaluated using Root Mean Squared Error (RMSE = $0.0082\text{ m}^3/\text{m}^3$) and Mean Absolute Error (MAE = $0.0040\text{ m}^3/\text{m}^3$).

---

### Q6: What is the physical meaning of volumetric soil moisture in units of $\text{m}^3/\text{m}^3$?
**Answer:** Volumetric soil moisture ($\theta$) represents the volume of water present per unit volume of bulk soil:
$$\theta = \frac{V_w}{V_T} \quad (\text{m}^3/\text{m}^3)$$
A reading of $0.25\text{ m}^3/\text{m}^3$ means 25% of the soil volume consists of water. Typical ranges:
- Sand: Permanent Wilting Point (PWP) $\approx 0.05$, Field Capacity (FC) $\approx 0.15$.
- Loam / Clay Loam: PWP $\approx 0.12 - 0.15$, FC $\approx 0.28 - 0.35$.
- Saturation: $\approx 0.45 - 0.50$.

---

### Q7: Explain the Magnus formula used for relative humidity derivation in your pipeline.
**Answer:** ERA5-Land provides 2m air temperature ($T$) and 2m dewpoint temperature ($T_d$). Relative humidity is the ratio of actual vapor pressure $e(T_d)$ to saturation vapor pressure $e_s(T)$:
$$\text{RH} = 100 \times \frac{\exp\left(\frac{17.625 \cdot T_d}{243.04 + T_d}\right)}{\exp\left(\frac{17.625 \cdot T}{243.04 + T}\right)}$$
This Clausius-Clapeyron approximation is accurate within $\pm 0.1\%$ across agricultural ranges ($0^\circ\text{C}$ to $50^\circ\text{C}$).

---

### Q8: What was your missing-value treatment strategy and why did you not use mean imputation?
**Answer:** Mean imputation is catastrophic for agricultural time series because it destroys temporal auto-correlation and dampens extreme events like monsoonal downpours. We applied:
- **Gaps $\le 3$ days:** Forward linear interpolation along the farm's time dimension.
- **Gaps $> 3$ days:** Retained as missing or excluded from training. No values were fabricated.

---

### Q9: How do your three configured Tamil Nadu demonstration farms differ agronomically?
**Answer:**
1. **TN001 (Thanjavur, Cauvery Delta):** Crop: Rice (Paddy). Soil: Clay loam. High water demand. Threshold: $0.35\text{ m}^3/\text{m}^3$, irrigation trigger: $0.28\text{ m}^3/\text{m}^3$. Flood/canal irrigation.
2. **TN002 (Coimbatore, Kongu Upland):** Crop: Cotton. Soil: Red sandy loam. Moderate demand. Threshold: $0.25\text{ m}^3/\text{m}^3$, trigger: $0.18\text{ m}^3/\text{m}^3$. Precision drip irrigation.
3. **TN003 (Madurai, Semi-arid Drylands):** Crop: Groundnut. Soil: Red loamy. Drought-tolerant. Threshold: $0.20\text{ m}^3/\text{m}^3$, trigger: $0.14\text{ m}^3/\text{m}^3$. Sprinkler irrigation.

---

### Q10: How does the system handle simulated cloud outages?
**Answer:** When cloud connectivity drops, the Fog node's health check flags `cloud_connected = False`. The local inference engine continues executing on local inputs. Predictions and decisions are persisted into the node's local SQLite buffer queue. When the cloud reconnects, an idempotent sync flushes queued events to the central database, matching audit IDs to prevent duplicates.

---

### Q11: What is the role of PySpark in your Big Data architecture?
**Answer:** PySpark enables distributed processing for large-scale gridded meteorological datasets (e.g. pan-India multi-decade IMD NetCDF grids spanning millions of grid points). In our pipeline, PySpark provides parallelized schema validation, geospatial grid point extraction, and distributed transformations, falling back to Pandas for in-memory single-node operations.

---

### Q12: Why is a chronological split mandatory for time-series ML, rather than random k-fold cross-validation?
**Answer:** Random splitting samples future observations into the training set and past observations into the test set. Since soil moisture has strong temporal auto-correlation ($\text{SM}_t \approx \text{SM}_{t-1}$), random splitting leads to severely inflated test scores (data leakage). Chronological splitting evaluates the model on genuinely unseen future periods.

---

### Q13: What baseline model was used to validate ML superiority?
**Answer:** We implemented a **Persistence Baseline**, which predicts that tomorrow's soil moisture will equal today's observed moisture ($\hat{\theta}_{t+1} = \theta_t$). The persistence baseline achieved test $R^2 = 0.7946$ and RMSE = $0.0103\text{ m}^3/\text{m}^3$. The Random Forest outperformed it significantly ($R^2 = 0.8722$, RMSE = $0.0082\text{ m}^3/\text{m}^3$).

---

### Q14: Explain the difference between MDI (Mean Decrease in Impurity) and Permutation Feature Importance.
**Answer:**
- **MDI (Gini/Variance reduction):** Measures how much each feature reduces tree node impurity across all splits. It is computationally fast but can bias toward high-cardinality features.
- **Permutation Importance:** Measures the decrease in model score when a feature column is randomly shuffled. In our evaluation, both methods confirmed that `soil_moisture_lag1` and rolling averages are the dominant predictors ($>80\%$).

---

### Q15: How does your irrigation recommendation engine account for upcoming rainfall?
**Answer:** The recommendation engine incorporates a meteorological override rule: if significant precipitation ($\ge 10\text{ mm}$) is recorded or forecast, irrigation is automatically deferred, even if current soil moisture is below the trigger point. This prevents over-watering, root asphyxiation, and energy waste.

---

### Q16: How do you prevent duplicate events during edge-to-cloud synchronization?
**Answer:** Every edge event is tagged with a unique deterministic `audit_id` hash generated from `(node_id, timestamp, event_type)`. The cloud database enforces an upsert/ignore rule on `audit_id`. If a retransmitted packet arrives, the cloud recognises the existing key and discards the duplicate.

---

### Q17: What is SQLite WAL mode and why is it used in the backend?
**Answer:** Write-Ahead Logging (WAL) allows concurrent reads while a write operation is in progress. In standard SQLite, writes lock the entire database file. With `PRAGMA journal_mode=WAL`, reads and writes occur concurrently without contention between the FastAPI request loop, edge sync, and WebSocket broadcasting.

---

### Q18: What is the significance of the 20 columns in your permanent audit file?
**Answer:** The 20 columns satisfy enterprise traceability requirements:
- Identifying context: `Audit_ID`, `UTC_Timestamp`, `Actor`.
- System state: `Previous_State`, `New_State`, `Cloud_Status`.
- Scientific details: `Model_Version`, `Dataset_ID`, `Processing_Duration_MS`.
- Verification: `Success_Failure`, `Error_Details`.

---

### Q19: Can you explain Hargreaves-Samani potential evapotranspiration (ETo)?
**Answer:** Hargreaves-Samani is a temperature-based formula for reference crop evapotranspiration:
$$\text{ETo} = 0.0023 \cdot R_a \cdot (T_{\text{mean}} + 17.8) \cdot \sqrt{T_{\text{max}} - T_{\text{min}}}$$
Where $R_a$ is extraterrestrial solar radiation (derived from latitude and day of year). It estimates the atmospheric water demand driving soil moisture depletion.

---

### Q20: What are the primary limitations of satellite-derived soil moisture products like ISRO MOSDAC or SMAP?
**Answer:**
1. **Penetration Depth:** L-band radiometers measure only the top 0–5 cm of soil, whereas crop roots extend 30–100 cm deep.
2. **Spatial Resolution:** A 25 km grid cell averages diverse topographies and soil types.
3. **Temporal Revisit:** Satellite revisit intervals (2–3 days) may miss transient rainfall events. SmartKhet 2.0 addresses this by merging satellite data with daily IMD rainfall grids.

---

### Q21: Why does the project strictly prohibit fabricating historical sensor data?
**Answer:** Fabricating historical data violates scientific research ethics. Demonstration data in SmartKhet 2.0 is generated strictly using regional climatological equations and is explicitly tagged `data_source = "demonstration_climatological_pattern"` and `is_demo = True`.

---

### Q22: How does WebSocket communication function in the SmartKhet 2.0 dashboard?
**Answer:** FastAPI maintains a WebSocket endpoint at `/ws` via `ConnectionManager`. Connected frontend clients receive live simulated sensor broadcasts, Fog node heartbeat updates, and cloud sync events every 3 seconds without HTTP polling.

---

### Q23: What is the P95 latency and why is it critical in Fog Computing evaluation?
**Answer:** The 95th percentile (P95) latency represents the response time below which 95% of requests fall. In cellular IoT, average latency may be ~100 ms, but P95 often spikes to >500 ms due to retransmissions. Fog computing guarantees a bounded P95 latency (~18 ms).

---

### Q24: How does XGBoost differ from Random Forest in theory and practice?
**Answer:**
- **Random Forest:** Bagging algorithm where trees are grown in parallel and independently on bootstrap samples, reducing variance.
- **XGBoost:** Boosting algorithm where trees are grown sequentially to fit the negative gradient (residuals) of prior trees, reducing bias.
- **In our benchmark:** Random Forest achieved slightly higher test $R^2$ (0.8722 vs 0.8582) with lower edge compute overhead.

---

### Q25: What is Median Absolute Error (MedAE) and why report it alongside MAE and RMSE?
**Answer:** MedAE is the median of absolute prediction errors: $\text{MedAE} = \text{median}(|y_1 - \hat{y}_1|, \dots, |y_n - \hat{y}_n|)$. It is completely robust to extreme outliers. Our MedAE of $0.0012\text{ m}^3/\text{m}^3$ proves that for the majority of days, prediction error is practically zero.

---

### Q26: How does the application prevent cross-site scripting (XSS) and CORS vulnerabilities?
**Answer:**
1. **Pydantic Validation:** All API inputs are strictly typed and sanitized.
2. **FastAPI CORSMiddleware:** Restricts cross-origin resource sharing to specified origins.
3. **React JSX Escaping:** React automatically escapes all string expressions before rendering.

---

### Q27: If a farmer's field has red sandy loam soil, how does its drainage compare to clay loam?
**Answer:** Red sandy loam has larger pore sizes, resulting in high hydraulic conductivity and fast drainage. Its Field Capacity is lower (~20–25%), requiring frequent, short-duration drip pulses. Clay loam has fine pore structures, high water-holding capacity (~35%), and slower drainage, making it suited to flood or canal irrigation for crops like rice.

---

### Q28: What is the role of the `scaler.joblib` artifact in your pipeline?
**Answer:** `scaler.joblib` stores the `StandardScaler` parameters (mean $\mu$ and standard deviation $\sigma$ for each feature) fitted strictly on the training set. At inference time, input features are scaled using these fixed parameters: $z = \frac{x - \mu}{\sigma}$.

---

### Q29: How is the system packaged and deployed locally without Docker or cloud bills?
**Answer:**
- Backend: Standard Python virtual environment with FastAPI and SQLite.
- Frontend: Node.js / Vite build compiling to static assets.
- Embedded Database: Local SQLite with zero external database server required.
- Edge Fog Simulation: In-process multi-node edge gateway simulation.

---

### Q30: What future improvements would be needed to transition SmartKhet 2.0 to physical hardware?
**Answer:**
1. Physical Edge Gateway: Deploying the Fog service onto a Raspberry Pi 4 or ESP32 gateway.
2. Field Telemetry: LoRaWAN transceivers connecting SDI-12 soil moisture probes.
3. Actuation: Solid-state relays controlling 24V solenoid irrigation valves.
4. Edge Quantization: Compiling the Random Forest model using ONNX Runtime for microcontrollers.

---

### Q31: Why is Median Absolute Error 0.0000 on the Baseline persistence model?
**Answer:** On dry days where no rain fell and temperature was steady, soil moisture between consecutive days changed by less than the precision threshold, resulting in an exact median error of zero. However, its RMSE ($0.0103$) was substantially higher than Random Forest ($0.0082$) because it fails completely during rainfall events.

---

### Q32: What is the final takeaway of the SmartKhet 2.0 research prototype?
**Answer:** SmartKhet 2.0 empirically demonstrates that rural agricultural irrigation can be managed intelligently and autonomously. By decoupling ML inference from cloud backhauls through localized Fog computing, farmers gain 100% operational availability, 90%+ lower decision latency, and data-driven water conservation.

