import os
import logging
import logging.config
import yaml
import pandas as pd

def load_raw_data(path, logger):
    """Load raw telecom churn dataset from CSV."""
    logger.info(f"Loading raw data from: {path}")
    if not os.path.exists(path):
        logger.error(f"Raw data file not found at {path}")
        raise FileNotFoundError(f"Raw data file not found at {path}")
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error reading CSV file at {path}: {e}")
        raise
    logger.info(f"Raw dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def validate_schema(df, logger):
    """Validate that all 21 expected columns are present with expected names."""
    logger.info("Validating schema — expecting 21 columns...")
    expected_cols = [
        "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
        "tenure", "PhoneService", "MultipleLines", "InternetService",
        "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
        "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
        "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn"
    ]
    
    if len(df.columns) != 21:
        raise ValueError(f"Schema Validation Error: Expected 21 columns, got {len(df.columns)}")
        
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Schema Validation Error: Expected column '{col}' is missing")
            
    logger.info("Schema validation passed: all 21 expected columns present")

def fix_whitespace_blanks(df, logger):
    """Scan string columns for whitespace/blank values, stripping spaces and replacing with NA."""
    logger.info("Scanning for whitespace/blank values in string columns...")
    df_copy = df.copy()
    object_cols = df_copy.select_dtypes(include=["object", "string"]).columns
    
    for col in object_cols:
        df_copy[col] = df_copy[col].astype(str).str.strip()
        blanks_mask = df_copy[col] == ""
        blanks_count = blanks_mask.sum()
        if blanks_count > 0:
            logger.warning(f"Column '{col}': {blanks_count} blank/whitespace value(s) found")
            df_copy.loc[blanks_mask, col] = pd.NA
            
    logger.info("Whitespace scan complete")
    return df_copy

def fix_total_charges(df, logger):
    """Convert TotalCharges to float64 and impute 0.0 where tenure == 0 and TotalCharges is NaN."""
    logger.info("Converting 'TotalCharges' from object to float64...")
    df_copy = df.copy()
    
    # Convert to numeric, coercing any blank strings (which are now pd.NA) to NaN
    df_copy["TotalCharges"] = pd.to_numeric(df_copy["TotalCharges"], errors="coerce")
    
    # Impute 0.0 only where tenure == 0 AND TotalCharges is NaN
    zero_tenure_nan_mask = (df_copy["tenure"] == 0) & df_copy["TotalCharges"].isna()
    impute_count = zero_tenure_nan_mask.sum()
    
    if impute_count > 0:
        df_copy.loc[zero_tenure_nan_mask, "TotalCharges"] = 0.0
        logger.info(f"Imputed TotalCharges = 0.0 for {impute_count} row(s) where tenure == 0 and TotalCharges is NaN")
    
    # Verify there are no remaining missing values in TotalCharges
    remaining_nan = df_copy["TotalCharges"].isna().sum()
    if remaining_nan > 0:
        raise ValueError(f"Data Quality Error: {remaining_nan} rows still contain NaN values in 'TotalCharges' after imputation.")
    else:
        logger.info("'TotalCharges' conversion complete — no remaining NaN values")
        
    return df_copy

def drop_duplicates(df, logger):
    """Drop duplicate records from DataFrame explicitly."""
    initial_rows = df.shape[0]
    df_clean = df.drop_duplicates(keep="first")
    dropped_count = initial_rows - df_clean.shape[0]
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} duplicate rows.")
    else:
        logger.info("Duplicate check passed: 0 duplicate rows found")
        
    return df_clean

def validate_cleaned_data(df, logger):
    """Verify data types, value bounds, and target distribution after cleaning."""
    logger.info("Performing post-clean data validation...")
    
    # 1. SeniorCitizen validation (must be 0 or 1 only)
    senior_citizen_vals = set(df["SeniorCitizen"].unique())
    if not senior_citizen_vals.issubset({0, 1}):
        raise ValueError(f"Validation Error: SeniorCitizen has unexpected values {senior_citizen_vals}")
        
    # 2. TotalCharges type validation
    if df["TotalCharges"].dtype != "float64":
        raise ValueError(f"Validation Error: Expected TotalCharges to be float64, got {df['TotalCharges'].dtype}")
        
    # 3. Log target class distribution
    churn_counts = df["Churn"].value_counts(dropna=False)
    churn_perc = df["Churn"].value_counts(normalize=True, dropna=False) * 100
    distribution_log = ", ".join([f"{val}: {count} ({perc:.2f}%)" for val, count, perc in zip(churn_counts.index, churn_counts.values, churn_perc.values)])
    logger.info(f"Churn Target Class Distribution: {distribution_log}")
    
    # 4. Check negative values for continuous variables
    for col in ["tenure", "MonthlyCharges", "TotalCharges"]:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            raise ValueError(f"Validation Error: Found {neg_count} negative value(s) in column '{col}'")
            
    logger.info(f"Post-cleaning validation passed. Shape: {df.shape[0]} rows, {df.shape[1]} columns")

def save_clean_data(df, path, logger):
    """Save cleaned dataset to destination path."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
    except Exception as e:
        logger.error(f"Error saving clean dataset to {path}: {e}")
        raise
    logger.info(f"Clean dataset saved to: {path} ({df.shape[0]} rows, {df.shape[1]} columns)")

def clean_pipeline(raw_path=None, processed_path=None, logger=None):
    """Main orchestrator for the data cleaning pipeline."""
    if logger is None:
        logger = logging.getLogger("ml.preprocessing.clean")
        
    logger.info("RetainIQ — Data Cleaning Pipeline START")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if raw_path is None:
        raw_path = os.path.join(base_dir, "data", "raw", "Telco_Customer_Churn.csv")
    if processed_path is None:
        processed_path = os.path.join(base_dir, "data", "processed", "telco_churn_clean.csv")
        
    try:
        df = load_raw_data(raw_path, logger)
        validate_schema(df, logger)
        df_clean = fix_whitespace_blanks(df, logger)
        df_clean = fix_total_charges(df_clean, logger)
        df_clean = drop_duplicates(df_clean, logger)
        validate_cleaned_data(df_clean, logger)
        save_clean_data(df_clean, processed_path, logger)
    except Exception as e:
        logger.error(f"Error during preprocessing pipeline: {e}")
        raise
        
    logger.info("RetainIQ — Data Cleaning Pipeline COMPLETE")
    return df_clean

if __name__ == "__main__":
    # Configure logging globally only when run as main script
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "configs", "logging_config.yaml"))
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        except Exception as e:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger("ml.preprocessing.clean").warning(
                f"Failed to load logging config from {config_path}, fallback to basicConfig: {e}"
            )
    else:
        logging.basicConfig(level=logging.INFO)
        
    main_logger = logging.getLogger("ml.preprocessing.clean")
    clean_pipeline(logger=main_logger)
