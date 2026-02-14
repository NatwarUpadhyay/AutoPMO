"""
Orchestrator Agent - Main Coordinator for AutoPMO

This agent is the central coordinator that receives user requests,
analyzes them, delegates to specialized agents, and synthesizes results.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain.tools import Tool

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent coordinates all other agents in AutoPMO.
    
    This is the "brain" of the system that:
    - Parses user intent
    - Determines which agents to invoke
    - Manages agent execution (parallel when possible)
    - Synthesizes multi-agent results
    - Handles error recovery
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Orchestrator",
            description="Central coordinator for all AutoPMO agents",
            **kwargs
        )
        
        # Registry of available agents
        self.agent_registry: Dict[str, BaseAgent] = {}
        
        # Agent delegation rules
        self.delegation_rules = {
            "create_project": ["planning", "risk", "infrastructure"],
            "assess_risk": ["risk", "infrastructure"],
            "generate_plan": ["planning", "risk"],
            "security_audit": ["audit", "infrastructure"],
            "status_update": ["communications"],
            "resource_allocation": ["planning", "infrastructure"],
        }
    
    def get_system_prompt(self) -> str:
        """System prompt for orchestrator."""
        return """You are the Orchestrator Agent for AutoPMO, an AI-powered Project Management Office.

Your role is to:
1. Understand user requests related to project management
2. Break down complex requests into subtasks
3. Delegate subtasks to specialized agents:
   - Planning Agent: Creates project plans, WBS, schedules
   - Risk Agent: Assesses and predicts project risks
   - Infrastructure Agent: Scans environments and resources
   - Communications Agent: Generates stakeholder updates
   - Audit Agent: Checks security and compliance

4. Coordinate agent execution (parallel when possible)
5. Synthesize results into a cohesive response
6. Provide actionable recommendations

Always think step-by-step:
- What is the user trying to accomplish?
- Which agents need to be involved?
- What information do they need?
- How should results be combined?

Be proactive in identifying risks and providing recommendations.
Use PM best practices (PMBOK, Agile, etc.) in your responses.
"""
    
    def register_tools(self) -> List[Tool]:
        """Register orchestrator tools."""
        tools = [
            Tool(
                name="delegate_to_agent",
                func=self._delegate_sync,
                description="Delegate a task to a specialized agent. Input should be JSON with 'agent_name' and 'task'"
            ),
            Tool(
                name="query_agent_status",
                func=self._query_status,
                description="Check the status of a running agent task"
            ),
            Tool(
                name="list_available_agents",
                func=self._list_agents,
                description="Get list of all available agents and their capabilities"
            ),
        ]
        return tools
    
    def register_agent(self, agent: BaseAgent):
        """
        Register a specialized agent with the orchestrator.
        
        Args:
            agent: Agent instance to register
        """
        agent_key = agent.name.lower().replace(" ", "_")
        self.agent_registry[agent_key] = agent
        logger.info(f"Registered {agent.name} with orchestrator")
    
    async def process_request(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user requests.
        
        Args:
            user_request: Natural language request from user
            context: Additional context (user_id, project_id, etc.)
            
        Returns:
            Synthesized response from multiple agents
        """
        logger.info(f"Orchestrator processing request: {user_request[:100]}...")
        
        # Classify intent
        intent = await self._classify_intent(user_request)
        logger.info(f"Classified intent: {intent}")
        
        # Determine which agents to invoke
        agents_needed = self.delegation_rules.get(intent, ["planning"])
        logger.info(f"Agents needed: {agents_needed}")
        
        # Prepare tasks for each agent
        agent_tasks = self._prepare_agent_tasks(
            intent, user_request, agents_needed, context
        )
        
        # Execute agents (in parallel where possible)
        results = await self._execute_agents_parallel(agent_tasks)
        
        # Synthesize results
        final_response = await self._synthesize_results(
            user_request, intent, results, context
        )
        
        return final_response
    
    async def _classify_intent(self, request: str) -> str:
        """
        Classify user intent from request.
        
        Args:
            request: User request text
            
        Returns:
            Intent classification
        """
        classification_prompt = f"""Classify this project management request into ONE category:

Request: {request}

Categories:
- create_project: Creating new project
- assess_risk: Risk assessment
- generate_plan: Project planning
- security_audit: Security/compliance check
- status_update: Status report
- resource_allocation: Resource planning

Respond with ONLY the category name, nothing else."""
        
        response = await self.chat(classification_prompt)
        return response.strip().lower()
    
    def _prepare_agent_tasks(
        self,
        intent: str,
        request: str,
        agents_needed: List[str],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prepare specific tasks for each agent.
        
        Args:
            intent: Classified intent
            request: Original user request
            agents_needed: List of agent names
            context: Request context
            
        Returns:
            List of agent task specifications
        """
        tasks = []
        
        for agent_name in agents_needed:
            if agent_name not in self.agent_registry:
                logger.warning(f"Agent {agent_name} not registered, skipping")
                continue
            
            # Customize task based on agent type
            if agent_name == "planning":
                task = f"Generate a project plan for: {request}"
            elif agent_name == "risk":
                task = f"Assess risks for: {request}"
            elif agent_name == "infrastructure":
                task = f"Analyze infrastructure requirements for: {request}"
            elif agent_name == "communications":
                task = f"Prepare stakeholder communication for: {request}"
            elif agent_name == "audit":
                task = f"Perform security audit for: {request}"
            else:
                task = request
            
            tasks.append({
                "agent_name": agent_name,
                "agent": self.agent_registry[agent_name],
                "task": task,
                "context": context
            })
        
        return tasks
    
    async def _execute_agents_parallel(
        self,
        agent_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agent_tasks: List of agent task specifications
            
        Returns:
            List of agent results
        """
        logger.info(f"Executing {len(agent_tasks)} agents in parallel")
        
        # Create coroutines
        coroutines = [
            task["agent"].execute(task["task"], task["context"])
            for task in agent_tasks
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_tasks[i]['agent_name']} failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _synthesize_results(
        self,
        original_request: str,
        intent: str,
        agent_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize results from multiple agents into a cohesive response.
        
        Args:
            original_request: Original user request
            intent: Classified intent
            agent_results: Results from all agents
            context: Request context
            
        Returns:
            Synthesized response
        """
        logger.info("Synthesizing results from all agents")
        
        # Prepare synthesis prompt
        results_text = "\n\n".join([
            f"Agent: {r['agent']}\nResult: {r['result']}"
            for r in agent_results
        ])
        
        synthesis_prompt = f"""Synthesize these agent results into a cohesive response.

Original Request: {original_request}
Intent: {intent}

Agent Results:
{results_text}

Create a comprehensive response that:
1. Directly answers the user's request
2. Combines insights from all agents
3. Highlights key findings and recommendations
4. Identifies any conflicts or concerns
5. Provides next steps

Format as a professional project management response."""
        
        synthesized_text = await self.chat(synthesis_prompt)
        
        return {
            "status": "success",
            "request": original_request,
            "intent": intent,
            "response": synthesized_text,
            "agent_results": agent_results,
            "recommendations": self._extract_recommendations(agent_results),
            "context": context
        }
    
    def _extract_recommendations(
        self,
        agent_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract key recommendations from agent results.
        
        Args:
            agent_results: Results from agents
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        for result in agent_results:
            if result.get("status") == "success":
                # Look for keywords in results
                text = str(result.get("result", "")).lower()
                
                if "high risk" in text or "critical" in text:
                    recommendations.append(f"⚠️ {result['agent']} identified critical concerns")
                
                if "security" in text and "vulnerability" in text:
                    recommendations.append(f"🔐 {result['agent']} found security issues")
        
        return recommendations
    
    def _delegate_sync(self, task_json: str) -> str:
        """Synchronous wrapper for delegation (for LangChain tool)."""
        # This is a simplified version for the tool interface
        return "Task delegated successfully"
    
    def _query_status(self, agent_name: str) -> str:
        """Query agent status."""
        if agent_name in self.agent_registry:
            agent = self.agent_registry[agent_name]
            return f"{agent.name} is available. History entries: {len(agent.history)}"
        return f"Agent {agent_name} not found"
    
    def _list_agents(self, query: str = "") -> str:
        """List available agents."""
        agents_info = [
            f"- {name}: {agent.description}"
            for name, agent in self.agent_registry.items()
        ]
        return "\n".join(agents_info)


# Convenience function to create fully configured orchestrator
def create_orchestrator(
    planning_agent: Optional[BaseAgent] = None,
    risk_agent: Optional[BaseAgent] = None,
    infrastructure_agent: Optional[BaseAgent] = None,
    communications_agent: Optional[BaseAgent] = None,
    audit_agent: Optional[BaseAgent] = None,
    **kwargs
) -> OrchestratorAgent:
    """
    Create orchestrator with all agents registered.
    
    Args:
        planning_agent: Planning agent instance
        risk_agent: Risk agent instance
        infrastructure_agent: Infrastructure agent instance
        communications_agent: Communications agent instance
        audit_agent: Audit agent instance
        **kwargs: Additional orchestrator configuration
        
    Returns:
        Configured orchestrator agent
    """
    orchestrator = OrchestratorAgent(**kwargs)
    
    if planning_agent:
        orchestrator.register_agent(planning_agent)
    if risk_agent:
        orchestrator.register_agent(risk_agent)
    if infrastructure_agent:
        orchestrator.register_agent(infrastructure_agent)
    if communications_agent:
        orchestrator.register_agent(communications_agent)
    if audit_agent:
        orchestrator.register_agent(audit_agent)
    
    return orchestrator
