from fastapi import APIRouter
from app.orchestration.engine import WorkflowManager

router = APIRouter()
orchestrator = WorkflowManager()

@router.get("/")
async def list_agents():
    return {"agents": orchestrator.available_agents()}
