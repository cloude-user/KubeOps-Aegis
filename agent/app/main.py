import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from agent.app.core.config import settings
from agent.app.api.auth import router as auth_router
from agent.app.api.routes import router as api_router
from agent.app.api.websocket import router as ws_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous SRE AI Agent Engine for Kubernetes (AKS) & Azure Cloud Self-Healing",
    version="2.0.0"
)

# Enable CORS for web frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)

# Mount & serve static Web Dashboard UI
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(os.path.join(web_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run(
        "agent.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
