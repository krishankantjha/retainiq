# RetainIQ Deployment Guide

This guide covers local and production deployment setups, container configurations, environment variables, and Alembic database migrations for the RetainIQ platform.

---

## Docker Compose Configuration

The standard production deployment uses a multi-container stack defined in `docker/docker-compose.yml`.

To start all services:
```bash
# Navigate to the docker directory
cd docker/

# Build and start services in detached mode
docker-compose up --build -d
```

---

## Environment Variables

The backend loads configuration dynamically from `backend/.env` or the shell environment:

| Variable | Type | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `APP_NAME` | String | `AI Customer Retention Platform API` | Branding label returned in the OpenAPI docs. |
| `APP_ENV` | String | `development` | Operational mode (`development` or `production`). |
| `JWT_SECRET` | String | `super-secret-key-change-in-production-1234567890` | Secret key used to sign session tokens. |
| `DATABASE_URL` | String | `sqlite:///./customer_retention.db` | SQL database connection URI. Resolves to an absolute path. |
| `ALLOWED_ORIGINS` | String | `http://localhost:8501,http://127.0.0.1:8501` | Comma-separated list of approved CORS origins. |

---

## Database Migrations

Database structures are version-controlled using **Alembic**. Migrations automatically execute on application startup if running in production mode.

To manually manage schema upgrades during development:
```bash
# Navigate to the backend directory
cd backend/

# Activate the virtual environment
source ../venv/Scripts/activate

# Apply migrations to the database
alembic upgrade head

# Generate a new migration script if database models changed
alembic revision --autogenerate -m "description_of_changes"
```
