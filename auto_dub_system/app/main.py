from fastapi import FastAPI
from app.api.routes import router as api_router
from app.config import settings

app = FastAPI(title="Auto Dub System")

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Auto Dub System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
