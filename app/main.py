# =============================================
# app/main.py
# =============================================
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "FastAPI Users API", "version": settings.version}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )