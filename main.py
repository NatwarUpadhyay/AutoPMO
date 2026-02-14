"""
AutoPMO FastAPI Application

Main API server for AutoPMO.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import (
    OrchestratorAgent,
    PlanningAgent,
    create_orchestrator
)
from agents.risk_agent import RiskAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.communications_agent import CommunicationsAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AutoPMO API",
    description="AI-Powered Project Management Office API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ProjectCreate(BaseModel):
    name: str
    description: str
    target_environment: Optional[str] = "openshift"
    budget: Optional[float] = None
    timeline_weeks: Optional[int] = 12

class AgentRequest(BaseModel):
    agent_type: str  # orchestrator, planning, risk, infrastructure, communications
    task: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    status: str
    agent: str
    result: Any
    execution_time: float

# Initialize agents (singleton pattern)
agents_initialized = False
orchestrator = None

def get_orchestrator() -> OrchestratorAgent:
    """Get or initialize orchestrator agent."""
    global orchestrator, agents_initialized
    
    if not agents_initialized:
        logger.info("Initializing agents...")
        
        # Create specialized agents
        planning = PlanningAgent()
        risk = RiskAgent()
        infrastructure = InfrastructureAgent()
        communications = CommunicationsAgent()
        
        # Create orchestrator with all agents
        orchestrator = create_orchestrator(
            planning_agent=planning,
            risk_agent=risk,
            infrastructure_agent=infrastructure,
            communications_agent=communications
        )
        
        agents_initialized = True
        logger.info("Agents initialized successfully")
    
    return orchestrator

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AutoPMO API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "projects": "/api/v1/projects",
            "agents": "/api/v1/agents/execute",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": "initialized" if agents_initialized else "not initialized"
    }

@app.post("/api/v1/projects", response_model=Dict[str, Any])
async def create_project(
    project: ProjectCreate,
    orch: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    Create a new project with AI-powered planning.
    """
    try:
        logger.info(f"Creating project: {project.name}")
        
        # Build request for orchestrator
        request = f"""Create a comprehensive project plan for: {project.name}

Description: {project.description}
Target Environment: {project.target_environment}
Budget: ${project.budget if project.budget else 'TBD'}
Timeline: {project.timeline_weeks} weeks

Please provide:
1. Work Breakdown Structure (WBS)
2. Risk Assessment
3. Resource Requirements
4. Infrastructure Analysis
5. Communication Plan
"""
        
        context = {
            "project_name": project.name,
            "budget": project.budget,
            "timeline_weeks": project.timeline_weeks
        }
        
        # Process with orchestrator
        result = await orch.process_request(request, context)
        
        return {
            "status": "success",
            "project_id": f"proj-{hash(project.name) % 10000}",
            "project_name": project.name,
            "ai_analysis": result
        }
        
    except Exception as e:
        logger.error(f"Project creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    orch: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    Execute a specific agent task.
    """
    try:
        logger.info(f"Executing {request.agent_type} agent")
        
        # Get the appropriate agent
        if request.agent_type == "orchestrator":
            result = await orch.process_request(request.task, request.context)
        elif request.agent_type == "planning":
            agent = orch.agent_registry.get("planning")
            result = await agent.execute(request.task, request.context)
        elif request.agent_type == "risk":
            agent = orch.agent_registry.get("risk")
            result = await agent.execute(request.task, request.context)
        elif request.agent_type == "infrastructure":
            agent = orch.agent_registry.get("infrastructure")
            result = await agent.execute(request.task, request.context)
        elif request.agent_type == "communications":
            agent = orch.agent_registry.get("communications")
            result = await agent.execute(request.task, request.context)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
        
        return AgentResponse(
            status=result.get("status", "success"),
            agent=result.get("agent", request.agent_type),
            result=result.get("result", result),
            execution_time=result.get("execution_time_seconds", 0)
        )
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/status")
async def get_agents_status(orch: OrchestratorAgent = Depends(get_orchestrator)):
    """Get status of all agents."""
    return {
        "orchestrator": {
            "name": orch.name,
            "registered_agents": list(orch.agent_registry.keys()),
            "history_count": len(orch.history)
        },
        "agents": {
            name: {
                "description": agent.description,
                "tools_count": len(agent.tools),
                "history_count": len(agent.history)
            }
            for name, agent in orch.agent_registry.items()
        }
    }

@app.get("/api/v1/agents/{agent_name}/history")
async def get_agent_history(
    agent_name: str,
    limit: int = 10,
    orch: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get execution history for a specific agent."""
    if agent_name == "orchestrator":
        return {"history": orch.get_history(limit)}
    
    agent = orch.agent_registry.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    return {"history": agent.get_history(limit)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

