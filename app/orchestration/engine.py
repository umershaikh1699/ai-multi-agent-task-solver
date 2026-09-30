from __future__ import annotations

import asyncio
import time
import traceback
from typing import Any, Dict

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from app.models.workflow import TaskRun, WorkflowRun, RunStatus, WorkflowSpec
from app.orchestration.graph import create_adjacency_and_indegree, layered_toposort
from app.agents.base import AgentFactory
from app.agents.tool_runner import ToolAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.specialized import SummarizerAgent, AnalysisAgent
from app.tools import default_tool_registry


class WorkflowManager:
    def __init__(self) -> None:
        self._executions: Dict[str, WorkflowRun] = {}
        self._toolset = default_tool_registry()
        self._agent_factory = AgentFactory()
        self._agent_factory.add(ToolAgent)
        self._agent_factory.add(PlanningAgent)
        self._agent_factory.add(SummarizerAgent)
        self._agent_factory.add(AnalysisAgent)

    def available_tools(self) -> Dict[str, Any]:
        return self._toolset.available()

    def available_agents(self) -> Dict[str, Any]:
        return self._agent_factory.available()

    def fetch_execution(self, execution_id: str) -> WorkflowRun | None:
        return self._executions.get(execution_id)

    async def start(self, execution_id: str, workflow: WorkflowSpec) -> WorkflowRun:
        timestamp = time.time()
        state = WorkflowRun(
            run_id=execution_id,
            status=RunStatus.PENDING,
            nodes={node.id: TaskRun(status=RunStatus.PENDING) for node in workflow.nodes},
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._executions[execution_id] = state
        asyncio.create_task(self._run_workflow(execution_id, workflow))
        return state

    async def _run_workflow(self, execution_id: str, workflow: WorkflowSpec) -> None:
        state = self._executions[execution_id]
        state.status = RunStatus.IN_PROGRESS
        state.updated_at = time.time()
        try:
            adjacency, in_degrees = create_adjacency_and_indegree(workflow)
            node_levels = layered_toposort(adjacency, in_degrees.copy())

            node_map = {node.id: node for node in workflow.nodes}
            node_outputs: Dict[str, Dict[str, Any]] = {}

            for group in node_levels:
                await asyncio.gather(
                    *[self._process_node(execution_id, node_map[node_id], node_outputs) for node_id in group]
                )

            state.status = (
                RunStatus.FAILED
                if any(n.status == RunStatus.FAILED for n in state.nodes.values())
                else RunStatus.COMPLETED
            )
        except Exception as exc:
            state.status = RunStatus.FAILED
            for result in state.nodes.values():
                if result.status == RunStatus.PENDING:
                    result.status = RunStatus.FAILED
                    result.error = "Workflow aborted due to orchestration error"
            state.nodes.setdefault(
                "_manager", TaskRun(status=RunStatus.FAILED, error=str(exc))
            )
        finally:
            state.updated_at = time.time()

    async def _process_node(self, execution_id: str, node_spec, node_outputs: Dict[str, Dict[str, Any]]) -> None:
        state = self._executions[execution_id]
        result = state.nodes[node_spec.id]
        result.started_at = time.time()
        result.status = RunStatus.IN_PROGRESS
        state.updated_at = time.time()

        agent_instance: Any = self._agent_factory.build(node_spec.agent.type)
        max_time = node_spec.agent.timeout_sec or 30.0
        max_retries = max(1, node_spec.agent.retries)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=0.25, min=0.5, max=3),
            reraise=True,
        ):
            with attempt:
                try:
                    result.attempts += 1
                    output = await asyncio.wait_for(
                        agent_instance.run(params=node_spec.params, inputs=node_outputs, tools=self._toolset),
                        timeout=max_time,
                    )
                    node_outputs[node_spec.id] = output
                    result.output = output
                    result.status = RunStatus.COMPLETED
                    result.completed_at = time.time()
                    result.logs.append(f"attempt={result.attempts} success")
                except Exception as err:
                    tb = traceback.format_exc(limit=3)
                    result.logs.append(f"attempt={result.attempts} error={err}")
                    result.error = str(err)
                    if result.attempts >= max_retries:
                        result.status = RunStatus.FAILED
                        result.completed_at = time.time()
                        raise
                finally:
                    self._executions[execution_id].updated_at = time.time()