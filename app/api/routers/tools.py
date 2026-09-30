from fastapi import APIRouter
from app.orchestration.engine import WorkflowManager

router = APIRouter()
orchestrator = WorkflowManager()

@router.get("/")
async def list_tools():
    return {"tools": orchestrator.available_tools()}
