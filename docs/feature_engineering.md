# RetainIQ Feature Ingestion & Transformations Guide

This guide outlines the feature engineering equations, categorical encoders, numerical scalers, and ingestion validation rules powering the RetainIQ pipeline. All calculations are implemented in [engineer.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/engineer.py).

---

## Feature Engineering Transformations

Raw customer records are transformed to extract 17 key predictors prior to model scoring:

### 1. `contract_is_mtm` (Binary Flag)
Identifies month-to-month contracts, which are highly correlated with churn:
$$\text{contract\_is\_mtm} = \mathbb{I}(\text{Contract} == \text{"Month-to-month"})$$

### 2. `tenure_bucket` (Categorical Bins)
Categorizes customer tenure into lifecycles:
$$\text{tenure\_bucket} \in \{\text{"0-12"}, \text{"12-24"}, \text{"24-48"}, \text{"48+"}\}$$

### 3. `is_early_stage` (Binary Flag)
Isolates newly onboarded customers in their first year:
$$\text{is\_early\_stage} = \mathbb{I}(\text{tenure} \le 12)$$

### 4. `auto_pay_flag` (Binary Flag)
Tracks auto-payment methods (reducing involuntary churn due to credit card expiration):
$$\text{auto\_pay\_flag} = \mathbb{I}(\text{PaymentMethod} \in \{\text{"Bank transfer (automatic)"}, \text{"Credit card (automatic)"}\})$$

### 5. `addon_count` (Continuous)
Sums the active internet security and value-added addons:
$$\text{addon\_count} = \sum \mathbb{I}(\text{Service} == \text{"Yes"})$$
*Evaluated over: `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, and `StreamingMovies`.*

### 6. `has_support` (Binary Flag)
Identifies tech support usage:
$$\text{has\_support} = \mathbb{I}(\text{TechSupport} == \text{"Yes"})$$

### 7. `security_over_streaming` (Binary Flag)
Identifies customers who prioritize device/data protection over media consumption:
$$\text{security\_over\_streaming} = \mathbb{I}(\text{protection\_count} > \text{streaming\_count})$$
*Where protection includes `OnlineSecurity`, `OnlineBackup`, and `DeviceProtection`, and streaming includes `StreamingTV` and `StreamingMovies`.*

### 8. `contract_early_stage_flag` (Binary Flag)
Flags high-risk new customers paying on monthly contracts:
$$\text{contract\_early\_stage\_flag} = \mathbb{I}(\text{Contract} == \text{"Month-to-month"} \land \text{tenure} \le 12)$$

### 9. `commitment_score` (Continuous Score)
A composite loyalty score weighting customer commitment based on contract length, tenure, and payment reliability:
$$\text{commitment\_score} = 1.96 \cdot \mathbb{I}(\text{Contract} \ne \text{"Month-to-month"}) + 0.46 \cdot \mathbb{I}(\text{auto\_pay\_flag}) + 0.58 \cdot \mathbb{I}(\text{tenure} > 12)$$

### 10. `premium_risk_flag` (Binary Flag)
Flags fiber optic customers paying monthly rates above the baseline training median:
$$\text{premium\_risk\_flag} = \mathbb{I}(\text{InternetService} == \text{"Fiber optic"} \land \text{MonthlyCharges} > \text{median\_charges})$$

### 11. `household_stability_flag` (Binary Flag)
Flags family/shared household accounts:
$$\text{household\_stability\_flag} = \mathbb{I}(\text{Partner} == \text{"Yes"} \land \text{Dependents} == \text{"Yes"})$$

### 12. `fiber_zero_engagement_flag` (Binary Flag)
Identifies fiber optic subscribers who have zero active internet addons:
$$\text{fiber\_zero\_engagement\_flag} = \mathbb{I}(\text{InternetService} == \text{"Fiber optic"} \land \text{addon\_count} == 0)$$

### 13. `high_charge_early_stage_flag` (Binary Flag)
Identifies high-spending customers in their first 12 months:
$$\text{high\_charge\_early\_stage\_flag} = \mathbb{I}(\text{MonthlyCharges} > \text{median\_charges} \land \text{tenure} \le 12)$$

### 14. `vulnerable_customer_flag` (Binary Flag)
Flags senior citizens living alone during their initial contract phase:
$$\text{vulnerable\_customer\_flag} = \mathbb{I}(\text{SeniorCitizen} == 1 \land \text{Partner} == \text{"No"} \land \text{Dependents} == \text{"No"} \land \text{tenure} \le 12)$$

### 15. `AvgMonthlyCharge` (Continuous spending intensity)
Average spending rate per month of tenure (uses `tenure + 1` to prevent division-by-zero errors):
$$\text{AvgMonthlyCharge} = \frac{\text{TotalCharges}}{\text{tenure} + 1}$$

### 16. `num_services` (Continuous service depth)
Total count of active customer subscriptions (phone, internet, backup, tech support, and streaming options):
$$\text{num\_services} = \text{phone\_active} + \text{internet\_active} + \text{backup\_active} + \text{support\_active} + \text{streaming\_active\_count}$$

### 17. `Contract` (Monotonic Ordinal Mapping)
Maps contract categories monotonically to months to preserve distance relationships:
$$\text{Contract} \rightarrow \begin{cases} 
1 & \text{if Month-to-month} \\ 
12 & \text{if One year} \\ 
24 & \text{if Two year} 
\end{cases}$$

---

## Ingestion Validation & Pipeline Rules

All telemetry uploads are validated against pipeline rules defined in [validator.py](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/preprocessing/validator.py) before scoring:

* **Type Assertion:** Continuous columns (such as charges and tenure) are cast to numeric values; nulls or whitespace errors are caught and flagged.
* **Categorical Validation:** Categorical attributes must match pre-approved domain lists (e.g., `Contract` must match `Month-to-month`, `One year`, or `Two year`).
* **Value Bounds:** Verifies that continuous values lie within logical constraints (e.g., charges must be non-negative, and tenure must be under $120$ months).
* **Leakage Prevention:** Imputation stats and scaling parameters are loaded directly from the serialized pipeline artifacts in [pipeline.pkl](file:///c:/Users/krish/Downloads/ai-customer-retention-platform/ml/artifacts/models/pipeline.pkl), preventing data leakage during cohort scoring.
