from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    target_env: Optional[str] = Field(None, description="Target environment e.g., aws, azure, gcp, openshift")
    description: Optional[str] = Field(None, description="Brief project description")


class Project(ProjectCreate):
    id: str
    wbs: Optional[dict] = None
    risk_assessment: Optional[dict] = None
    tasks: List[dict] = []
    charter_url: Optional[str] = None
    raci_matrix: Optional[dict] = None


class AgentTask(BaseModel):
    agent: str = Field(..., description="Name of the agent to execute e.g., planning, risk, infrastructure, communications")
    payload: dict = Field(default_factory=dict, description="Task input for the agent")


class ModelPredictRequest(BaseModel):
    model: str = Field(..., description="Model identifier e.g., risk_predictor, velocity_forecaster")
    features: dict = Field(default_factory=dict, description="Feature map for prediction")


app = FastAPI(
    title="AutoPMO API",
    version="0.1.0",
    description="Minimal MVP API skeleton for AutoPMO",
)


# --- In-memory stores (MVP-only) ---
PROJECTS: Dict[str, Project] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "autopmo-api"}


@app.post("/api/v1/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate):
    project_id = str(uuid4())
    project = Project(id=project_id, **payload.dict())

    # MVP logic placeholders
    # In a real implementation these would be delegated to agents and models
    project.wbs = {"phase": "Assessment", "tasks": []}
    project.risk_assessment = {"probability": 0.2, "impact": 2, "category": "schedule"}
    project.tasks = []

    PROJECTS[project_id] = project
    return project


@app.get("/api/v1/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/v1/agents/execute")
def execute_agent(task: AgentTask) -> dict:
    # Stubbed agent execution for MVP
    if task.agent.lower() == "planning":
        return {
            "agent": "planning",
            "result": {
                "wbs": {
                    "phase": "Planning",
                    "tasks": [
                        {"id": "WBS-1.1", "name": "Infrastructure Discovery", "effort_hours": 40},
                        {"id": "WBS-1.2", "name": "Security Audit", "effort_hours": 32},
                    ],
                }
            },
        }
    elif task.agent.lower() == "risk":
        return {
            "agent": "risk",
            "result": {
                "risk": {
                    "probability": 0.35,
                    "impact": 3,
                    "category": "technical",
                    "mitigations": [
                        "Pair senior with junior engineers",
                        "Spike on unfamiliar components",
                    ],
                }
            },
        }
    else:
        return {"agent": task.agent, "result": {"message": "Agent stub executed", "payload": task.payload}}


@app.get("/api/v1/models/predict")
def model_predict(model: str, **features) -> dict:
    # MVP stub: return a deterministic placeholder
    if model == "risk_predictor":
        score = 0.42
        return {"model": model, "prediction": {"risk_score": score, "label": "medium"}, "features": features}
    return {"model": model, "prediction": {"message": "model stub"}, "features": features}


# Optional: local dev entrypoint
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
