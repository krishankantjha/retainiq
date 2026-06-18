"""
Preprocessing pipeline module for RetainIQ.

Defines the ColumnTransformer, splits the data into train and test sets,
applies the feature engineering from engineer.py, fits the preprocessing encoders,
and serializes the artifacts for training and inference.
"""

import logging
import logging.config
import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from ml.preprocessing.engineer import engineer_features

logger = logging.getLogger("ml.preprocessing.pipeline")

# Column groups for the ColumnTransformer
NUMERIC_COLS = ["tenure", "MonthlyCharges", "addon_count", "commitment_score"]
ORDINAL_COLS = ["tenure_bucket"]
ORDINAL_CATEGORIES = [["0-12", "12-24", "24-48", "48+"]]

CATEGORICAL_COLS = [
    "gender",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaymentMethod",
]

BINARY_COLS = [
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "PaperlessBilling",
    "contract_is_mtm",
    "is_early_stage",
    "auto_pay_flag",
    "has_support",
    "contract_early_stage_flag",
    "premium_risk_flag",
    "household_stability_flag",
    "security_over_streaming",
    "fiber_zero_engagement_flag",
    "high_charge_early_stage_flag",
    "vulnerable_customer_flag",
]


def run_pipeline(clean_csv_path: str, artifacts_dir: str, processed_dir: str) -> None:
    """
    Runs the full preprocessing pipeline on the cleaned dataset.
    Loads, splits, engineers features, fits/transforms scaling/encoding,
    and serializes the artifacts.
    """
    logger.info("Starting preprocessing pipeline run")

    # Ensure output directories exist
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Load clean data
    if not os.path.exists(clean_csv_path):
        raise FileNotFoundError(f"Clean CSV file not found at: {clean_csv_path}")
    
    df = pd.read_csv(clean_csv_path)
    logger.info(f"Loaded clean dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    # Separate features and target
    if "Churn" not in df.columns:
        raise ValueError("Target column 'Churn' not found in clean dataset")

    X = df.drop(columns=["Churn"])
    y = df["Churn"]

    # Stratified split to preserve target class distribution
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )
    logger.info(f"Split data into Train: {X_train.shape[0]} rows, Test: {X_test.shape[0]} rows")

    # Compute median MonthlyCharges on training set only to prevent data leakage
    train_monthly_charges_median = float(X_train["MonthlyCharges"].median())
    logger.info(f"Calculated training MonthlyCharges median: {train_monthly_charges_median:.2f}")

    # Apply feature engineering to both splits using the training median
    train_full = X_train.assign(Churn=y_train.values)
    test_full = X_test.assign(Churn=y_test.values)

    train_engineered = engineer_features(train_full, train_monthly_charges_median)
    test_engineered = engineer_features(test_full, train_monthly_charges_median)

    # Separate target from features again
    y_train_final = train_engineered.pop("Churn")
    y_test_final = test_engineered.pop("Churn")

    # Set up the preprocessing transformations
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_COLS),
            ("ordinal", OrdinalEncoder(categories=ORDINAL_CATEGORIES, handle_unknown="use_encoded_value", unknown_value=-1), ORDINAL_COLS),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLS),
            ("binary", "passthrough", BINARY_COLS),
        ],
        remainder="drop"
    )

    # Fit preprocessor only on the training set
    preprocessor.fit(train_engineered)
    logger.info("Fitted ColumnTransformer on training features")

    # Transform both datasets
    X_train_transformed = preprocessor.transform(train_engineered)
    X_test_transformed = preprocessor.transform(test_engineered)

    # Get output feature names
    feature_names = preprocessor.get_feature_names_out()

    # Reconstruct processed DataFrames
    train_df = pd.DataFrame(X_train_transformed, columns=feature_names)
    train_df["Churn"] = y_train_final.values

    test_df = pd.DataFrame(X_test_transformed, columns=feature_names)
    test_df["Churn"] = y_test_final.values

    # Save processed DataFrames to disk
    train_csv_path = os.path.join(processed_dir, "train_features.csv")
    test_csv_path = os.path.join(processed_dir, "test_features.csv")
    
    train_df.to_csv(train_csv_path, index=False)
    test_df.to_csv(test_csv_path, index=False)
    logger.info(f"Saved processed training features to: {train_csv_path}")
    logger.info(f"Saved processed test features to: {test_csv_path}")

    # Save fitted ColumnTransformer
    pipeline_path = os.path.join(artifacts_dir, "pipeline.pkl")
    with open(pipeline_path, "wb") as f:
        pickle.dump(preprocessor, f)
    logger.info(f"Saved pipeline artifact to: {pipeline_path}")

    # Save additional metadata needed for inference
    encoders_meta = {
        "train_monthly_charges_median": train_monthly_charges_median,
        "feature_names_out": list(feature_names),
        "numeric_cols": NUMERIC_COLS,
        "ordinal_cols": ORDINAL_COLS,
        "categorical_cols": CATEGORICAL_COLS,
        "binary_cols": BINARY_COLS,
        "train_shape": list(train_df.shape),
        "test_shape": list(test_df.shape),
    }

    encoders_path = os.path.join(artifacts_dir, "encoders.pkl")
    with open(encoders_path, "wb") as f:
        pickle.dump(encoders_meta, f)
    logger.info(f"Saved encoder metadata to: {encoders_path}")


def load_pipeline(artifacts_dir: str) -> tuple:
    """
    Loads and returns the fitted preprocessing pipeline and associated metadata.
    """
    pipeline_path = os.path.join(artifacts_dir, "pipeline.pkl")
    encoders_path = os.path.join(artifacts_dir, "encoders.pkl")

    if not os.path.exists(pipeline_path) or not os.path.exists(encoders_path):
        raise FileNotFoundError("Pipeline or encoder metadata files not found.")

    with open(pipeline_path, "rb") as f:
        preprocessor = pickle.load(f)

    with open(encoders_path, "rb") as f:
        metadata = pickle.load(f)

    return preprocessor, metadata


if __name__ == "__main__":
    import yaml

    # Configure logging based on local settings or defaults
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    config_path = os.path.join(base_dir, "configs", "logging_config.yaml")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            logging.config.dictConfig(yaml.safe_load(f))
    else:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s | %(levelname)s | %(message)s")

    clean_csv = os.path.join(base_dir, "data", "processed", "telco_churn_clean.csv")
    artifacts = os.path.join(base_dir, "ml", "artifacts")
    processed = os.path.join(base_dir, "data", "processed")

    try:
        run_pipeline(clean_csv, artifacts, processed)
        print("Pipeline execution succeeded.")
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        raise
