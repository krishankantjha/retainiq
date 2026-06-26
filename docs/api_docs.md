# RetainIQ API Specification & Endpoints Guide

This reference guide details the REST API endpoints exposed by the FastAPI backend server. It covers user authentication, churn forecasting, explainability queries, counterfactual simulations, cohort uploads, and system health status.

---

## Authorization

All endpoints under the `/api/v1` namespace (except `/api/v1/auth/login`) require authentication via a JWT bearer token passed in the header:

```http
Authorization: Bearer <your-jwt-token>
```

---

## System Verification

### `GET /health`
Verifies backend server state and database connectivity.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  {
    "status": "ok"
  }
  ```
* **Error Response (500 Internal Server Error)**:
  ```json
  {
    "detail": "Database connection degraded: <error-message>"
  }
  ```

---

## Authentication

### `POST /api/v1/auth/login`
Authenticates user credentials and returns a secure JWT access token.

* **Request Body (JSON)**:
  ```json
  {
    "username": "admin",
    "password": "password"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
* **Error Response (401 Unauthorized)**:
  ```json
  {
    "detail": "Invalid username or password"
  }
  ```

---

## Predictions & Explainability

### `GET /api/v1/predict/explain/{customer_id}`
Retrieves continuous behavioral telemetry, calibrated churn risk probabilities, local SHAP explanations, and recommended retention campaigns for a specific customer ID.

* **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `customer_id` | String | Yes | Unique customer identifier (e.g. `1234-ABCD`). |

* **Success Response (200 OK)**:
  ```json
  {
    "customer_id": "1234-ABCD",
    "churn_probability": 0.3852,
    "is_high_risk": true,
    "demographics": {
      "Gender": "Male",
      "Tenure": 24,
      "Contract": "Month-to-month",
      "MonthlyCharges": 95.50
    },
    "top_drivers": [
      {
        "feature": "numeric__MonthlyCharges",
        "shap_value": 0.32
      }
    ],
    "save_plays": [
      {
        "feature": "numeric__MonthlyCharges",
        "play_name": "Billing Rate Audit",
        "recommendation": "Perform invoice review and offer proactive loyalty credit."
      }
    ]
  }
  ```

### `POST /api/v1/predict/counterfactual`
Generates counterfactual simulations by projecting tweaked telemetry variables onto the Autoencoder bottleneck representation.

* **Request Body (JSON)**:
  ```json
  {
    "customer_id": "1234-ABCD",
    "tweaks": {
      "Contract": "One year",
      "MonthlyCharges": 85.0
    }
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "customer_id": "1234-ABCD",
    "original_probability": 0.725,
    "simulated_probability": 0.384,
    "risk_reduction_pct": 47.03,
    "annual_revenue_saved": 120.0
  }
  ```

### `GET /api/v1/predict/autocomplete`
Searches customer IDs matching a given prefix.

* **Query Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `query` | String | Yes | Search prefix prefix string (e.g., `12`). |

* **Success Response (200 OK)**:
  ```json
  [
    "1234-ABCD",
    "1290-XYZ"
  ]
  ```

### `POST /api/v1/predict/upload`
Uploads a telemetry cohort CSV file for asynchronous batch ingestion and prediction.

* **Request Body (Multipart Form)**:
  | Field | Type | Description |
  | :--- | :---: | :--- |
  | `file` | Binary | CSV file object representing the customer cohort. |

* **Success Response (202 Accepted)**:
  ```json
  {
    "upload_id": 1,
    "status": "processing",
    "filename": "telco_june_cohort.csv",
    "row_count": 0
  }
  ```

### `GET /api/v1/predict/upload/status/{upload_id}`
Checks the processing status and record count logs of a batch cohort upload.

* **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `upload_id` | Integer | Yes | Unique database primary key of the uploaded task. |

* **Success Response (200 OK)**:
  ```json
  {
    "upload_id": 1,
    "status": "completed",
    "row_count": 7043,
    "error_message": null
  }
  ```

---

## Analytics & Aggregates

### `GET /api/v1/analytics/overview`
Retrieves aggregated churn and revenue metric KPIs for the executive dashboard.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  {
    "total_customers": 7043,
    "churn_rate": 0.265,
    "average_risk": 0.312,
    "high_risk_count": 1860,
    "annualized_mrr_at_stake": 1420500.00
  }
  ```

### `GET /api/v1/analytics/save-plays`
Lists campaign descriptions and recommendations from the Save Playbook catalog.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "play_name": "Billing Rate Audit",
      "trigger_field": "numeric__MonthlyCharges",
      "action": "Offer proactive loyalty discount."
    }
  }
  ```

### `GET /api/v1/analytics/cohort`
Queries active database records for custom cohorts analysis.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "customer_id": "1234-ABCD",
      "tenure": 24,
      "monthly_charges": 95.50,
      "contract": "Month-to-month",
      "payment_method": "Electronic check",
      "churn_probability": 0.38,
      "cluster": 0
    }
  ]
  ```

### `GET /api/v1/analytics/model-health`
Returns feature distribution drift statistics and overall model monitoring KPIs.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  {
    "status": "Healthy",
    "model_name": "Weighted Ensemble Churn Classifier",
    "model_version": "1.1.0",
    "drift_ratio": 0.052,
    "message": "Operational features remain within training baseline distributions.",
    "drift_details": {
      "numeric__tenure": {
        "method": "ks_test",
        "ks_statistic": 0.024,
        "p_value": 0.854,
        "drifted": false
      }
    }
  }
  ```

### `GET /api/v1/analytics/diagnostics-metadata`
Retrieves model validation metrics (ROC curves, precision, recall) for model diagnostics.

* **Request Parameters**: None.
* **Success Response (200 OK)**:
  ```json
  {
    "accuracy": 0.842,
    "roc_auc": 0.844,
    "precision": 0.524,
    "recall": 0.808,
    "f1_score": 0.636
  }
  ```
