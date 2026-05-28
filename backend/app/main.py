from fastapi import FastAPI

app = FastAPI(title="AI Customer Retention Platform API")


@app.get("/health")
def health():
    return {"status": "ok"}
