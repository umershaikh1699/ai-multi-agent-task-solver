# Wand AI - Multi-Agent Task Solver

A powerful FastAPI service that converts natural language requests into executable multi-agent workflows. It features an intelligent Planning Agent, a robust Execution Engine, and a real-time UI.

---

## Features

- **Natural Language Planning**: The `PlanningAgent` (powered by Groq LLM) converts plain English requests into structured workflows.
- **Intelligent Clarification**: If a request is ambiguous, the agent asks for clarification, merging your answers with the previous context.
- **Multi-Agent Execution**: Orchestrates specialized agents:
    - `http.get`: Fetches data from APIs.
    - `agent.analysis`: Filters and analyzes data.
    - `agent.summarizer`: Condenses information.
- **Real-time UI**: Watch workflows execute step-by-step with a live dashboard.
- **Resilient**: Supports retries, timeouts, and dependency management.

---

## Design Decisions

- **FastAPI Framework**: For high-performance async execution and easy API definition.
- **Agentic Architecture**: Decouples "Planning" (LLM) from "Execution" (Deterministic Tools).
- **In-Memory State**: Lightweight state management for rapid prototyping (can be swapped for DB).
- **Pydantic Models**: Strict schema validation ensures safety between agents.

---

## Endpoints

### Workflows
- **POST** `/workflows/from-text`  
  Submit a natural language request (e.g., "Get quotes from dummyjson").
  
- **POST** `/workflows/`  
  Submit a raw JSON workflow specification.

- **GET** `/workflows/{run_id}`
  Retrieve the status and output of a workflow run.

### Health
- **GET** `/health`  
  Service health check.

---

## Project Structure

```
app/
  ├── agents/           # Agent implementations (Planning, Specialized)
  │   ├── planning_agent.py
  │   └── specialized.py
  ├── orchestration/    # execution engine & graph logic
  │   └── engine.py
  ├── prompts/          # System prompts
  │   └── planning.py
  ├── static/           # Frontend UI (HTML/JS)
  └── main.py           # App entrypoint
```

---

## Getting Started

### 1. Configure Environment
Create a `.env` file with your Groq API key:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000` to use the interactive dashboard.

### 4. Run Tests
```bash
pytest -v
```
