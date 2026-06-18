"""
Model Explainability & Actionable Save Plays Service.

Computes local feature contributions (SHAP values) for a customer's prediction
and maps the top positive drivers of churn to business retention plays.
"""

import os
import logging
import pandas as pd
import shap

logger = logging.getLogger("backend.app.ml.explain")

# Mapping of feature signatures to prescriptive business campaigns
SAVE_PLAY_MAPPING = {
    "Contract_Month-to-month": (
        "1-Year Contract Lock Campaign",
        "Offer a monthly rate discount to transition the customer from Month-to-Month to a stable 1-Year contract."
    ),
    "contract_is_mtm": (
        "1-Year Contract Lock Campaign",
        "Offer a monthly rate discount to transition the customer from Month-to-Month to a stable 1-Year contract."
    ),
    "PaymentMethod_Electronic check": (
        "Auto-Pay Conversion Promotion",
        "Offer a one-time $5 bill credit to set up an automatic payment method (Credit Card or Bank Transfer) to reduce payment friction."
    ),
    "fiber_zero_engagement_flag": (
        "Add-on Bundling Campaign",
        "Propose bundling free Online Security and Device Protection for 3 months to increase service stickiness and engagement."
    ),
    "MonthlyCharges": (
        "Billing Rate Audit",
        "Perform a billing audit to identify unused features and downgrade to a cheaper plan or offer a $10/month loyalty discount."
    ),
    "high_charge_early_stage_flag": (
        "Billing Rate Audit",
        "Perform a billing audit to identify unused features and downgrade to a cheaper plan or offer a $10/month loyalty discount."
    ),
    "vulnerable_customer_flag": (
        "Priority Onboarding Support",
        "Connect the customer with a dedicated technical support specialist to assist with home device setup and contract onboarding."
    ),
    "InternetService_Fiber optic": (
        "Fiber Performance Check",
        "Contact the customer to verify line speed satisfaction and offer a free tech-health router audit."
    ),
    "OnlineSecurity_No": (
        "Security Add-on Upsell",
        "Send promotional materials outlining security services and offer a 30-day free trial of Online Security."
    ),
    "TechSupport_No": (
        "Premium Support Promotion",
        "Highlight priority technical support channels and offer 1 month of free premium assistance."
    ),
    "tenure": (
        "Early Stage Loyalty Welcome",
        "Customer is in the early tenure phase. Send a personalized account check-in call to address initial configuration issues."
    )
}


def explain_customer_churn(customer_df: pd.DataFrame, model, feature_names_in: list, top_n: int = 3) -> dict:
    """
    Computes local SHAP values for a single customer record and extracts the top features
    contributing to their churn risk score. Returns SHAP values and mapped save plays.
    """
    logger.info("Starting SHAP explanation for customer record")

    # Extract base estimator from CalibratedClassifierCV if model is calibrated
    if hasattr(model, "calibrated_classifiers_"):
        base_estimator = model.calibrated_classifiers_[0].estimator
    else:
        base_estimator = model

    # Ensure input customer dataframe columns align with the model's features
    customer_aligned = customer_df[feature_names_in]

    try:
        # Create TreeExplainer for XGBoost model
        explainer = shap.Explainer(base_estimator)
        shap_values = explainer(customer_aligned)
        
        # Get raw feature contributions (SHAP values) for the first record
        contributions = shap_values.values[0]
        
        # Pair feature names with their SHAP contributions
        feature_impacts = list(zip(feature_names_in, contributions))
        
        # Filter for positive impacts (drivers pushing towards churn)
        positive_drivers = [item for item in feature_impacts if item[1] > 0]
        
        # Sort in descending order of contribution magnitude
        positive_drivers.sort(key=lambda x: x[1], reverse=True)
        
        # Extract top N drivers
        top_drivers = positive_drivers[:top_n]
        
        # Map top drivers to Save Plays
        save_plays = []
        for feature, val in top_drivers:
            # Check matches against mapped rules
            matched = False
            for key, play in SAVE_PLAY_MAPPING.items():
                if key in feature:
                    save_plays.append({
                        "feature": feature,
                        "contribution": float(val),
                        "play_name": play[0],
                        "recommendation": play[1]
                    })
                    matched = True
                    break
            
            # Default fallback play if no specific mapping matches
            if not matched:
                save_plays.append({
                    "feature": feature,
                    "contribution": float(val),
                    "play_name": "General Loyalty Outreach",
                    "recommendation": f"Initiate check-in call addressing customer satisfaction regarding feature: {feature}."
                })

        explanation = {
            "success": True,
            "top_drivers": [{"feature": f, "shap_value": float(v)} for f, v in top_drivers],
            "save_plays": save_plays
        }
        return explanation

    except Exception as e:
        logger.error(f"SHAP explanation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "top_drivers": [],
            "save_plays": []
        }
