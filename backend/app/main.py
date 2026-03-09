from fastapi import FastAPI

app = FastAPI()

# health_check endpoint (docker-composeのヘルスチェックで使用)
@app.get("/health")
def health_check():
    return {"status": "ok"}