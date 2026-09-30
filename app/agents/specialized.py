"""Specialized agents for summarization, analysis, and visualization."""
from __future__ import annotations

import json
import os

from typing import Any, Dict

from app.agents.base import AgentInterface
from app.services.llm_service import GroqLLMService
from app.tools.base import ToolRegistry

# --- Summarizer Agent ---

class SummarizerAgent:
    """Agent that condenses text or data into a summary."""
    type = "agent.summarizer"
    
    def __init__(self) -> None:
        self._llm = GroqLLMService()
        
    async def run(
        self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry
    ) -> Dict[str, Any]:
        text = params.get("text")
        data = params.get("data")
        
        # Resolve inputs from previous nodes if needed
        input_from = params.get("input_from")
        if input_from and input_from in inputs:
            prev_output = inputs[input_from]
            # Try to intelligently extract meaningful content from previous output
            if isinstance(prev_output, dict):
                # If there's a 'picked' key (from json.pick), use that
                if "picked" in prev_output:
                    data = prev_output["picked"]
                # Else if there's a 'json' key (from http.get), use that
                elif "json" in prev_output:
                    data = prev_output["json"]
                # Else if there's 'text' use that
                elif "text" in prev_output:
                    text = prev_output["text"]
                else:
                    data = prev_output

        content_to_summarize = ""
        if text:
            content_to_summarize = f"Text:\n{text}"
        elif data:
            content_to_summarize = f"Data:\n{json.dumps(data, indent=2)}"
        else:
            raise ValueError("No text or data provided for summarization")
            
        system_prompt = "You are a concise summarizer. Summarize the provided content clearly and briefly."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_to_summarize}
        ]
        
        summary = await self._llm.generate(messages=messages)
        return {"summary": summary}


# --- Analysis Agent ---

class AnalysisAgent:
    """Agent that performs logical analysis on data."""
    type = "agent.analysis"
    
    def __init__(self) -> None:
        self._llm = GroqLLMService()
        
    async def run(
        self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry
    ) -> Dict[str, Any]:
        data = params.get("data")
        query = params.get("query", "Analyze this data and identify key patterns.")
        
        # Resolve inputs
        input_from = params.get("input_from")
        if input_from and input_from in inputs:
            prev_output = inputs[input_from]
            if isinstance(prev_output, dict):
                if "picked" in prev_output:
                    data = prev_output["picked"]
                elif "json" in prev_output:
                    data = prev_output["json"]
                else:
                    data = prev_output
        
        if not data:
            raise ValueError("No data provided for analysis")

        system_prompt = "You are a data analyst. Analyze the provided data logicially and answer the user's query."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nData:\n{json.dumps(data, indent=2)}"}
        ]
        
        analysis = await self._llm.generate(messages=messages)
        return {"analysis": analysis}



