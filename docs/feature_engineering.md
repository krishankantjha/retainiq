# RetainIQ Feature Ingestion & Transformations Guide

This guide outlines the feature engineering pipeline, categorical encoders, numerical scalers, and ingestion validation rules powering the RetainIQ platform.

---

## Feature Engineering Transformations

Raw customer records are processed via [engineer.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/engineer.py) to generate several key indicators:

1. **`addon_count`** (Continuous):
   Sums the optional ecosystem security and media services subscribed to by the customer:
   
   $$\text{addon\_count} = \sum \mathbb{I}(\text{Service} == \text{"Yes"})$$
   
   Monitored services include: `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, and `StreamingMovies`.

2. **`commitment_score_v2`** (Continuous):
   Computes a weighted customer longevity score using coefficients extracted from feature magnitude tests:
   
   $$\text{commitment\_score\_v2} = 1.96 \cdot \mathbb{I}(\text{Contract} \ne \text{"Month-to-month"}) + 0.58 \cdot \mathbb{I}(\text{Tenure} > 12) + 0.46 \cdot \mathbb{I}(\text{PaymentMethod} == \text{"Auto-Pay"})$$

3. **`security_over_streaming`** (Continuous Ratio):
   Evaluates ecosystem security priorities against streaming consumption:
   
   $$\text{security\_over\_streaming} = \frac{\mathbb{I}(\text{OnlineSecurity} == \text{"Yes"}) + \mathbb{I}(\text{OnlineBackup} == \text{"Yes"}) + 1.0}{\mathbb{I}(\text{StreamingTV} == \text{"Yes"}) + \mathbb{I}(\text{StreamingMovies} == \text{"Yes"}) + 1.0}$$

4. **`vulnerable_customer_flag`** (Binary):
   Identifies newly onboarded customers paying premium rates under monthly contract terms:
   
   $$\text{vulnerable\_customer\_flag} = \mathbb{I}(\text{Tenure} \le 3) \land \mathbb{I}(\text{Contract} == \text{"Month-to-month"}) \land \mathbb{I}(\text{MonthlyCharges} \ge 70.0)$$

---

## Ingestion Validation & Pipeline Rules

All telemetry uploads are validated against pipeline rules defined in [validator.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/validator.py) before scoring:

* **Type Assertion:** Continuous columns (such as charges and tenure) are cast to numeric values; nulls or whitespace errors are caught and flagged.
* **Categorical Validation:** Categorical attributes must match pre-approved domain lists (e.g., `Contract` must match `Month-to-month`, `One year`, or `Two year`).
* **Value Bounds:** Verifies that continuous values lie within logical constraints (e.g., charges must be non-negative, and tenure must be under $120$ months).
* **Leakage Prevention:** Imputation stats and scaling parameters are loaded directly from the serialized pipeline artifacts in [encoders.pkl](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/artifacts/encoders.pkl), preventing data leakage during cohort scoring.
