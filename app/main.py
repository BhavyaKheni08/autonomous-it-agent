from fastapi import FastAPI
from app.api.routes import router as tickets_router

app = FastAPI(title="Auto-IT-Support Agent System")

app.include_router(tickets_router, prefix="/api/v1", tags=["Tickets"])

@app.get("/")
def health_check():
    return {"status": "running", "system": "Auto-IT-Support"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
