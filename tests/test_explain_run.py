import sys
import os
import pickle
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.ml.explain import explain_customer_churn

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
artifacts_dir = os.path.join(base_dir, "ml", "artifacts")
processed_dir = os.path.join(base_dir, "data", "processed")

model = pickle.load(open(os.path.join(artifacts_dir, "model.pkl"), "rb"))
meta = pickle.load(open(os.path.join(artifacts_dir, "model_metadata.pkl"), "rb"))
test_df = pd.read_csv(os.path.join(processed_dir, "test_features.csv"))

X_test = test_df.drop(columns=["Churn"])
features = meta["feature_names_in"]

# Take customer record index 0
customer_record = X_test.iloc[[0]]

explanation = explain_customer_churn(customer_record, model, features)
print("SUCCESS:", explanation["success"])
print("Top Drivers:", explanation["top_drivers"])
print("Save Plays:")
for play in explanation["save_plays"]:
    print(f" - Feature: {play['feature']}")
    print(f"   Contribution: {play['contribution']:.4f}")
    print(f"   Play Name: {play['play_name']}")
    print(f"   Recommendation: {play['recommendation']}")
