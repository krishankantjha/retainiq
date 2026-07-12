# Customer Segmentation Personas & Profiles

This document outlines the customer behavioral segments identified via K-Means++ clustering on natural, continuous feature coordinates. 

---

## Behavioral Personas Overview

### Cluster 0: Moderate-Value, Budget-Conscious Users
* **Size**: 1214 customers (21.55% of training set)
* **Average Churn Rate**: **7.25%**
* **Scaled Behavioral Scores**:
  * Tenure: -0.092 (Low tenure)
  * Monthly Charges: -1.454 (Low monthly billing)
  * Ecosystem Services: -1.315 (Low ecosystem lock-in)
* **Description**: Medium-tenure customers paying low-to-moderate monthly charges with moderate ecosystem services. This represents your budget-conscious core user base.
* **Retention Save Play Strategy**: Trigger Auto-Pay conversion and cross-sell technical security add-ons to improve retention friction.

---

### Cluster 1: New Churn-Risk Users
* **Size**: 2523 customers (44.78% of training set)
* **Average Churn Rate**: **44.95%**
* **Scaled Behavioral Scores**:
  * Tenure: -0.713 (Low tenure)
  * Monthly Charges: +0.141 (High monthly billing)
  * Ecosystem Services: -0.057 (Low ecosystem lock-in)
* **Description**: Short-tenure customers with high initial monthly charges, short contract types, and low ecosystem subscription counts. This represents your highest churn-risk group.
* **Retention Save Play Strategy**: Prioritize direct welcome onboarding check-ins, rate audits, and transition them to long-term contract lock-in campaigns.

---

### Cluster 2: High-Value Premium Cohort
* **Size**: 1897 customers (33.67% of training set)
* **Average Churn Rate**: **14.39%**
* **Scaled Behavioral Scores**:
  * Tenure: +1.007 (High tenure)
  * Monthly Charges: +0.743 (High monthly billing)
  * Ecosystem Services: +0.917 (High ecosystem lock-in)
* **Description**: Long-tenure customers with high ecosystem service counts and high monthly billing rates. This is your most valuable premium group.
* **Retention Save Play Strategy**: Ensure high-priority VIP customer support. Check fiber router performance and offer loyalty credits proactively.

---

