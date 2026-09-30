from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class RunStatus(str, Enum):
    """Overall execution states."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task(BaseModel):
    """A single node/task in the workflow."""
    type: str = Field(...)
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout_sec: Optional[float] = Field(default=15.0)
    retries: int = Field(default=1)


class NodeSpec(BaseModel):
    """A single node/task in the workflow."""
    id: str
    agent: Task
    params: Dict[str, Any] = Field(default_factory=dict)

class Connection(BaseModel):
    """Directed edge from one task to another."""
    source: str
    target: str

class WorkflowSpec(BaseModel):
    """Workflow definition submitted by the client."""
    model_config = ConfigDict(extra="forbid")
    nodes: List[NodeSpec]
    edges: List[Connection] = Field(default_factory=list)

class TaskRun(BaseModel):
    """Runtime record of a task."""
    status: RunStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempts: int = 0
    logs: List[str] = Field(default_factory=list)

class WorkflowRun(BaseModel):
    """State of an executing workflow."""
    run_id: str
    status: RunStatus
    nodes: Dict[str, TaskRun]
    created_at: float
    updated_at: float


class NaturalLanguageRequest(BaseModel):
    """Request for generating a workflow from natural language."""
    request: str
    context: Optional[str] = None


class WorkflowGenerationResponse(BaseModel):
    """Response from workflow generation endpoint."""
    run_id: Optional[str] = None
    status: str = "PENDING"
    clarification: Optional[str] = None
    original_request: str
    workflow_spec: Optional[WorkflowSpec] = None
