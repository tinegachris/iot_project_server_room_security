from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Server Room Monitoring API",
    description="API endpoints for reporting and retrieving logs, and for manual control of the server room monitoring system.",
    version="1.0.0"
)

# All API routes are included under the /api prefix
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
