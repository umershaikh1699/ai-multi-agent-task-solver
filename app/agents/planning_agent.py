"""Planning agent that converts natural language to workflow specifications."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.agents.base import AgentInterface
from app.models.workflow import WorkflowSpec
from app.services.llm_service import GroqLLMService
from app.tools.base import ToolRegistry
from app.prompts.planning import PLANNING_SYSTEM_PROMPT


class PlanningAgent:
    """Agent that uses LLM to generate workflow specifications from natural language."""
    
    type = "planning.agent"
    
    def __init__(self) -> None:
        """Initialize planning agent with LLM service."""
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not api_key:
             # In a real app we might raise an error, but here we'll let the service fail or use its own check
             pass

        # Ensure model is set to one that supports JSON mode well
        self._llm = GroqLLMService(api_key=api_key, model=model)
    
    async def run(
        self,
        *,
        params: Dict[str, Any],
        inputs: Dict[str, Any],
        tools: ToolRegistry,
    ) -> Dict[str, Any]:
        """Generate workflow specification from natural language request.
        
        Args:
            params: Must contain 'request' (str) - the natural language request
            
        Returns:
            Dict containing 'workflow_spec' (WorkflowSpec | None) and 'clarification' (str | None)
        """
        request = params.get("request")
        if not request:
            raise ValueError("params.request is required")
        
        # Include context if provided (e.g., previous Q&A)
        context = params.get("context", "")
        full_query = request
        if context:
            full_query = f"Previous Context:\n{context}\n\nCurrent Request:\n{request}"
        
        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": full_query},
        ]
        
        # Generate JSON
        try:
            response_json = await self._llm.generate_json(
                messages=messages,
                temperature=0.2,
                max_tokens=512,
                retries=3,
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to generate workflow: {e}")
        
        # Handle Clarification
        if "clarification" in response_json and response_json["clarification"]:
            return {
                "workflow_spec": None,
                "clarification": response_json["clarification"],
                "raw_response": json.dumps(response_json, indent=2),
            }
            
        # Handle Workflow
        if "workflow" in response_json:
            workflow_data = response_json["workflow"]
        else:
             # Fallback if LLM didn't wrap in "workflow" key but returned schema directly
            workflow_data = response_json

        # Validate and parse into WorkflowSpec
        try:
            workflow_spec = WorkflowSpec(**workflow_data)
        except Exception as e:
            raise ValueError(f"Invalid workflow specification: {e}\nGenerated JSON: {json.dumps(response_json, indent=2)}")
        
        return {
            "workflow_spec": workflow_spec.model_dump(),
            "clarification": None,
            "raw_response": json.dumps(response_json, indent=2),
        }
