# RetainIQ — AI-Powered Customer Retention Intelligence Platform

RetainIQ is a production-grade machine learning platform built to predict, analyze, and mitigate customer churn. The platform uses classification models trained on customer subscription data (modeled after the IBM Telco Churn dataset) and translates risk signals into actionable "Save Plays" to protect Monthly Recurring Revenue (MRR).

---

## Key Features

* **Real-Time Inference API:** Generates instant churn risk scores, risk levels (High, Medium, Low), and top behavioral churn drivers.
* **Asynchronous Batch Inference:** Supports drag-and-drop CSV uploads via the Streamlit interface, processing cohorts concurrently with background workers.
* **Explainable AI (XAI):** Explains model decisions transparently using local SHAP values to identify exact churn drivers.
* **Prescriptive Save Plays:** Matches customer risk profiles with targeted retention campaigns (such as prompting payment upgrades or contract migrations).
* **Interactive Executive Dashboard:** Visualizes key performance indicators (KPIs), churn trends, revenue impact, and segment risk splits.
* **Multi-Container Architecture:** Orchestrated via Docker Compose with Nginx routing requests, managing static resources, and handling WebSocket connections.

---

## Repository Structure

```text
ai-customer-retention-platform/
├── backend/                  # FastAPI web server
│   ├── app/
│   │   ├── api/              # Routers and rate limiters
│   │   ├── core/             # Configuration, logging, and security
│   │   ├── database/         # SQLAlchemy models and migrations
│   │   ├── ml/               # Inference engine (SHAP explainers, model loaders)
│   │   └── services/         # Core business logic services
│   ├── tests/                # Pytest integration tests
│   └── requirements.txt      # Python dependencies list
├── frontend/                 # Streamlit analytical dashboard
│   ├── app.py                # Main portal entrypoint and router
│   ├── api_client.py         # REST API connector class
│   ├── requirements.txt      # UI python requirements
│   └── views/                # Tab sub-view implementations
├── ml/                       # Machine Learning pipelines
│   ├── notebooks/            # EDA, engineering, and modeling notebooks
│   ├── preprocessing/        # Data validation and feature pipelines
│   ├── training/             # Fitting, hyperparameter tuning, and evaluation
│   └── artifacts/            # Serialized models and scaling pipelines
├── configs/                  # Global YAML logging and model parameters
├── docker/                   # Compose files and Nginx reverse proxy configurations
├── docs/                     # Architecture manuals and domain translations
├── data/                     # Raw and processed datasets (ignored by git)
└── scripts/                  # Automated setup and seeding scripts
```

---

## Getting Started

### Prerequisites
* Python 3.9+ (Python 3.11 recommended)
* Git Bash, WSL, or a macOS/Linux terminal

### 1. Initialize the Environment
Run the setup script from the project root to initialize a virtual environment, upgrade package managers, and install dependencies:
```bash
./scripts/setup.sh
```

### 2. Configure Environment Variables
Open the generated `backend/.env` file and replace the `JWT_SECRET` placeholder with a secure random key:
```env
JWT_SECRET="your-secure-random-token-here"
```

### 3. Local Databases
The repository maintains two SQLite databases for local development:
* `backend/customer_retention.db`: The primary database used by the FastAPI server and the `pytest` suite.
* `customer_retention.db` (Project Root): A fallback database used by standalone preprocessing and machine learning scripts.

Both database files are required for compatibility. Do not delete or move them.

### 4. Run the Applications

#### Start the FastAPI Backend
```bash
cd backend
source ../venv/Scripts/activate # Windows Git Bash
# source ../venv/bin/activate   # Linux/macOS
uvicorn app.main:app --reload
```
The API documentation will be available at: http://localhost:8000/docs

#### Start the Streamlit Dashboard
```bash
cd frontend
source ../venv/Scripts/activate # Windows Git Bash
# source ../venv/bin/activate   # Linux/macOS
streamlit run app.py
```
The dashboard interface will open at: http://localhost:8501

---

## License
Distributed under the MIT License. See [LICENSE](LICENSE) for more details.