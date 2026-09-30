from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

from app.api.routers.health import router as health_router
from app.api.routers.workflows import router as workflows_router
from app.api.routers.tools import router as tools_router
from app.api.routers.agents import router as agents_router

# Create FastAPI app instance
def create_app() -> FastAPI:
    app = FastAPI(title="WandAI Orchestrator")
    
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    app.include_router(health_router)
    app.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
    app.include_router(tools_router, prefix="/tools", tags=["tools"])
    app.include_router(agents_router, prefix="/agents", tags=["agents"])
    return app


# Initialize the FastAPI app
app = create_app()

# root endpoint
@app.get("/", summary="Dashboard")
async def root():
    return FileResponse("app/static/index.html")