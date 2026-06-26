# RetainIQ — Project History & Development Ledger

This document logs the development history, design decisions, model iterations, and business trade-off analyses for the RetainIQ platform.

---

## Phase 0: Project Foundation

We began by stabilizing the repository structure and correcting licensing information to align with open-source compliance standards.

---

## Phase 1: Data Ingestion & Validation

We established a type-safe and side-effect-free ingestion pipeline.
- **Pipeline Isolation (`clean.py`):** Rewrote the cleaning scripts to run operations on copy dataframes (`df.copy()`) rather than modifying objects in place.
- **Schema Validation:** Replaced standard Python `assert` blocks with explicit exception raising (`ValueError`) to prevent validation bypasses under optimized executions.
- **Zero-Tenure Imputation:** Targeted zero-tenure entries for null `TotalCharges` handling. Missing values are imputed to `0.0` specifically for new clients, avoiding the demographic bias introduced by aggregate statistical averages.

---

## Phase 1.5: Exploratory Data Analysis & Statistical Audits

We updated the prototyping notebooks with statistical tests to mathematically validate customer churn drivers.
- **Dynamic Path Resolution:** Updated file links to resolve dynamically based on execution context.
- **Bivariate Analysis:** Added correlation heatmaps, Mann-Whitney U tests for continuous features (tenure, billing charges), and Chi-Square tests to verify relationships between categorical fields (contract types, internet features) and churn.

---

## Phase 2: Feature Engineering & Preprocessing

We constructed feature transformation steps and prevented training-serving data leakage.
- **Redundancy Resolution:** Replaced the redundant placeholder feature `protection_score` (which duplicated information in `addon_count`) with a calculated `security_over_streaming` ratio.
- **Leakage Control:** Implemented scikit-learn pipeline elements (`ColumnTransformer` and scaling steps) that fit strictly on training splits. Scaling objects are serialized as [encoders.pkl](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/artifacts/encoders.pkl) for serving consistency.

---

## Phase 3: Model Training & Feature Pruning

We optimized model architectures and performed feature selection.
- **Evidence-Based Weighting (`commitment_score_v2`):** Modeled tenure and contract types using logistic regression to extract coefficients ($1.96$ for non-month-to-month contracts, $0.58$ for tenure $>12$ months, and $0.46$ for auto-pay). These coefficients are used directly in calculating the updated commitment score.
- **Feature Pruning:** Analyzed feature importances on the XGBoost baseline. Dropped redundant features like `binary__has_support` (which sat in the bottom $5.9\%$ of importances and contributed $0.0$ to ROC-AUC) to optimize execution complexity.

---

## Phase 3.5: Model Calibration & Balancing

We addressed class imbalance and calibrated probabilities.
- **Class Imbalance:** Compared balancing methods on the validation sets. XGBoost trained with `scale_pos_weight` dynamically set to $2.77$ yielded the highest validation metrics (ROC-AUC: $0.844$, Recall: $80.75\%$, F1-score: $0.636$).
- **Calibration:** Wrapped the model in a cross-validated calibration pipeline (`CalibratedClassifierCV`) using isotonic regression, reducing the Brier score to $0.1367$.
- **Business Utility Optimization:** Evaluated the economic impact of retention campaigns. We selected a prediction threshold of $0.25$, saving an estimated $98\%$ of peak benefits while decreasing campaign outreach overhead by $25\%$ compared to the raw default threshold.

---

## Phase 4: Evaluation & Local Explainability

We finalized model metrics and set up the local explainability framework.
- **SHAP Integrations:** Programmed local SHAP value calculations in [explain.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/backend/app/ml/explain.py) to attribute feature contributions for individual profiles.
- **Retention Save Playbook:** Designed a mapping framework to route high-risk SHAP drivers to prescriptive campaigns (e.g. Month-to-month contracts $\rightarrow$ Annual lock-in offers; high charges $\rightarrow$ Billing rate audit).

---

## Technical Directory Reference Map

All implemented components are accessible via the directory tree below:

* **Data Cleaning:** [clean.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/clean.py)
* **Feature Engineering:** [engineer.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/engineer.py)
* **Pipeline Transformer:** [pipeline.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/pipeline.py)
* **GridSearch Tuning:** [tune.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/training/tune.py)
* **Model Training:** [train.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/training/train.py)
* **Model Evaluation:** [evaluate.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/training/evaluate.py)
* **Explainability Interface:** [explain.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/backend/app/ml/explain.py)
