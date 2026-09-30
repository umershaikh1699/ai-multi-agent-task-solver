from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
from app.models.workflow import WorkflowSpec, WorkflowRun, NaturalLanguageRequest, WorkflowGenerationResponse
from app.orchestration.engine import WorkflowManager

router = APIRouter()
orchestrator = WorkflowManager()

@router.post("/", response_model=WorkflowRun)
async def submit_workflow(spec: WorkflowSpec):
    """Accept a workflow definition and create a new run record."""
    workflow_id = str(uuid4())
    return await orchestrator.start(workflow_id, spec)


@router.post("/from-text")
async def submit_natural_language_workflow(request: NaturalLanguageRequest):
    """Convert natural language request to workflow and execute it.
    
    This endpoint uses the PlanningAgent to convert plain text requests
    into structured workflow specifications, then executes them.
    
    If the request is ambiguous, returns status=NEEDS_CLARIFICATION.
    """
    try:
        # Use PlanningAgent to generate workflow
        planning_agent = orchestrator._agent_factory.build("planning.agent")
        
        # Parse params
        params = {"request": request.request}
        if request.context:
            params["context"] = request.context

        plan_result = await planning_agent.run(
            params=params,
            inputs={},
            tools=orchestrator._toolset,
        )
        
        # Check for clarification request
        if plan_result.get("clarification"):
            return JSONResponse(content={
                "status": "NEEDS_CLARIFICATION",
                "clarification": plan_result["clarification"],
                "original_request": request.request
            })
            
        workflow_spec_data = plan_result["workflow_spec"]
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Convert dictionary to WorkflowSpec model to ensure validity
    try:
        spec = WorkflowSpec(**workflow_spec_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generated invalid workflow: {e}")

    # Submit for execution
    try:
        # Use the correct method from WorkflowManager (start -> returns WorkflowRun)
        workflow_id = str(uuid4())
        workflow_run = await orchestrator.start(workflow_id, spec)
        
        return JSONResponse(content={
            "run_id": workflow_run.run_id,
            "status": "PENDING",
            "original_request": request.request,
            "workflow_spec": spec.model_dump(),
            "nodes": {k: v.model_dump() for k, v in workflow_run.nodes.items()}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {e}")


@router.get("/{workflow_id}", response_model=WorkflowRun)
async def get_workflow(workflow_id: str):
    """Retrieve a workflow run by ID."""
    run = orchestrator.fetch_execution(workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return JSONResponse(content=run.model_dump())
