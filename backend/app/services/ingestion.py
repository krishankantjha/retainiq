import os
import logging
import pandas as pd
import numpy as np
from configs.dataset_config import config_loader
from ml.preprocessing.clean import fix_whitespace_blanks, fix_total_charges, drop_duplicates

logger = logging.getLogger("backend.app.services.ingestion")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
artifacts_dir_relative = config_loader.training["data_paths"].get("artifacts_dir", "ml/artifacts")
artifacts_dir = os.path.join(PROJECT_ROOT, artifacts_dir_relative)


def log_prediction_events(customer_ids: list, y_probs: np.ndarray, is_high_risks: np.ndarray, cluster_labels: np.ndarray):
    """
    Appends predictions audit trail to monthly-partitioned JSONL files.
    Files are rotated monthly (prediction_logs_YYYY-MM.jsonl)
    to prevent a single file growing unboundedly in production.
    """
    import json
    from datetime import datetime
    metrics_dir = os.path.join(artifacts_dir, "metrics")
    os.makedirs(metrics_dir, exist_ok=True)

    # Monthly rotation: each calendar month gets its own file
    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")
    log_path = os.path.join(metrics_dir, f"prediction_logs_{month_str}.jsonl")

    timestamp = now.isoformat() + "Z"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            for i, cid in enumerate(customer_ids):
                record = {
                    "timestamp": timestamp,
                    "customer_id": str(cid),
                    "churn_probability": float(y_probs[i]),
                    "is_high_risk": bool(is_high_risks[i]),
                    "cluster": int(cluster_labels[i])
                }
                f.write(json.dumps(record) + "\n")
        logger.info(f"Successfully logged {len(customer_ids)} predictions to audit trail: {log_path}")
    except Exception as e:
        logger.error(f"Failed to write prediction logs to audit trail: {e}")


def clean_uploaded_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applies basic data cleaning matching the ML data cleaning steps."""
    logger.info("Cleaning uploaded dataframe...")
    df_clean = df.copy()
    
    # Standardize columns casing to match expected
    col_mapping = {
        "customerid": "customerID",
        "seniorcitizen": "SeniorCitizen",
        "phoneservice": "PhoneService",
        "multiplelines": "MultipleLines",
        "internetservice": "InternetService",
        "onlinesecurity": "OnlineSecurity",
        "onlinebackup": "OnlineBackup",
        "deviceprotection": "DeviceProtection",
        "techsupport": "TechSupport",
        "streamingtv": "StreamingTV",
        "streamingmovies": "StreamingMovies",
        "paperlessbilling": "PaperlessBilling",
        "paymentmethod": "PaymentMethod",
        "monthlycharges": "MonthlyCharges",
        "totalcharges": "TotalCharges",
        "churn": "Churn"
    }
    # Apply casing standardization for any columns that might be lowercase
    df_clean = df_clean.rename(columns=lambda c: col_mapping.get(c.lower(), c))
    
    target_col = config_loader.feature.get("target_column", "Churn")
    # 21 columns required (or 20 if Churn is missing, we'll insert a placeholder Churn)
    if target_col not in df_clean.columns:
        df_clean[target_col] = None
        
    df_clean = fix_whitespace_blanks(df_clean, logger)
    df_clean = fix_total_charges(df_clean, logger)
    df_clean = drop_duplicates(df_clean, logger)
    
    # Reset index to ensure 0-based sequential row indexing
    df_clean = df_clean.reset_index(drop=True)
    return df_clean
