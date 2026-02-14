"""
Planning Agent - Project Planning and WBS Generation

This agent is responsible for:
- Generating Work Breakdown Structures (WBS)
- Creating project schedules
- Resource allocation
- Timeline estimation
- Critical path analysis
"""

import logging
import yaml
from typing import Any, Dict, List
from datetime import datetime, timedelta

from langchain.tools import Tool

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """
    Planning Agent generates project plans, WBS, and schedules.
    
    Uses ML models for:
    - Velocity forecasting
    - Effort estimation
    - Dependency analysis
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Planning",
            description="Generates project plans, WBS, and schedules using PM best practices",
            **kwargs
        )
    
    def get_system_prompt(self) -> str:
        """System prompt for planning agent."""
        return """You are the Planning Agent for AutoPMO, an expert in project planning.

Your expertise includes:
- PMBOK standards and best practices
- Agile/Scrum methodologies
- Work Breakdown Structure (WBS) creation
- Critical Path Method (CPM)
- Resource allocation
- Effort estimation

When creating plans:
1. Start with high-level phases
2. Break down into detailed tasks
3. Estimate effort realistically
4. Identify dependencies
5. Assign appropriate resources
6. Calculate critical path
7. Add buffer for risks

Output Format:
- Use YAML for structured data
- Include task IDs, descriptions, estimates
- Specify dependencies clearly
- Note resource requirements

Follow PMI standards and use industry best practices.
Be realistic about timelines and include appropriate buffers.
"""
    
    def register_tools(self) -> List[Tool]:
        """Register planning tools."""
        tools = [
            Tool(
                name="generate_wbs",
                func=self._generate_wbs,
                description="Generate Work Breakdown Structure for a project. Input: project description"
            ),
            Tool(
                name="estimate_effort",
                func=self._estimate_effort,
                description="Estimate effort for tasks. Input: task description and complexity"
            ),
            Tool(
                name="calculate_critical_path",
                func=self._calculate_critical_path,
                description="Calculate critical path from task dependencies"
            ),
            Tool(
                name="allocate_resources",
                func=self._allocate_resources,
                description="Suggest resource allocation for tasks"
            ),
        ]
        return tools
    
    def _generate_wbs(self, project_description: str) -> str:
        """
        Generate Work Breakdown Structure.
        
        Args:
            project_description: Description of the project
            
        Returns:
            WBS in YAML format
        """
        logger.info(f"Generating WBS for: {project_description[:100]}")
        
        # In production, this would call the ML model
        # For now, return a structured template
        
        wbs = {
            "project": {
                "name": "Cloud Migration Project",
                "duration_weeks": 12,
                "phases": [
                    {
                        "id": "1.0",
                        "name": "Assessment",
                        "duration_weeks": 2,
                        "tasks": [
                            {
                                "id": "1.1",
                                "name": "Infrastructure Discovery",
                                "effort_hours": 40,
                                "assigned_to": "infrastructure_team",
                                "dependencies": []
                            },
                            {
                                "id": "1.2",
                                "name": "Application Analysis",
                                "effort_hours": 60,
                                "assigned_to": "development_team",
                                "dependencies": ["1.1"]
                            },
                            {
                                "id": "1.3",
                                "name": "Security Audit",
                                "effort_hours": 32,
                                "assigned_to": "security_team",
                                "dependencies": ["1.1"]
                            }
                        ]
                    },
                    {
                        "id": "2.0",
                        "name": "Planning",
                        "duration_weeks": 2,
                        "tasks": [
                            {
                                "id": "2.1",
                                "name": "Architecture Design",
                                "effort_hours": 80,
                                "assigned_to": "architecture_team",
                                "dependencies": ["1.2", "1.3"]
                            },
                            {
                                "id": "2.2",
                                "name": "Migration Strategy",
                                "effort_hours": 40,
                                "assigned_to": "project_manager",
                                "dependencies": ["2.1"]
                            }
                        ]
                    },
                    {
                        "id": "3.0",
                        "name": "Execution",
                        "duration_weeks": 6,
                        "tasks": [
                            {
                                "id": "3.1",
                                "name": "Environment Setup",
                                "effort_hours": 80,
                                "assigned_to": "devops_team",
                                "dependencies": ["2.2"]
                            },
                            {
                                "id": "3.2",
                                "name": "Application Migration",
                                "effort_hours": 200,
                                "assigned_to": "development_team",
                                "dependencies": ["3.1"]
                            },
                            {
                                "id": "3.3",
                                "name": "Data Migration",
                                "effort_hours": 120,
                                "assigned_to": "database_team",
                                "dependencies": ["3.1"]
                            }
                        ]
                    },
                    {
                        "id": "4.0",
                        "name": "Testing & Validation",
                        "duration_weeks": 2,
                        "tasks": [
                            {
                                "id": "4.1",
                                "name": "Integration Testing",
                                "effort_hours": 80,
                                "assigned_to": "qa_team",
                                "dependencies": ["3.2", "3.3"]
                            },
                            {
                                "id": "4.2",
                                "name": "Performance Testing",
                                "effort_hours": 60,
                                "assigned_to": "qa_team",
                                "dependencies": ["4.1"]
                            },
                            {
                                "id": "4.3",
                                "name": "Security Testing",
                                "effort_hours": 40,
                                "assigned_to": "security_team",
                                "dependencies": ["4.1"]
                            }
                        ]
                    }
                ]
            }
        }
        
        return yaml.dump(wbs, default_flow_style=False, sort_keys=False)
    
    def _estimate_effort(self, task_info: str) -> str:
        """
        Estimate effort for a task.
        
        Args:
            task_info: Task description and complexity
            
        Returns:
            Effort estimate with justification
        """
        # In production, this would use ML model for velocity forecasting
        # For now, return template
        
        return """Effort Estimate:
- Optimistic: 40 hours
- Most Likely: 60 hours
- Pessimistic: 90 hours
- Expected (PERT): 62 hours

Factors considered:
- Task complexity: Medium
- Team experience: High
- Technology familiarity: Medium
- Dependencies: 2 tasks
- Risk buffer: 15%

Recommendation: Allocate 3 sprints with 1 developer"""
    
    def _calculate_critical_path(self, dependencies: str) -> str:
        """
        Calculate critical path.
        
        Args:
            dependencies: Task dependency graph
            
        Returns:
            Critical path analysis
        """
        return """Critical Path Analysis:
Critical Path: 1.1 → 1.2 → 2.1 → 2.2 → 3.1 → 3.2 → 4.1 → 4.2
Total Duration: 85 days
Float Available: Tasks 1.3, 3.3, 4.3 have 5-10 days float

Recommendations:
1. Focus resources on critical path tasks
2. Use float for risk mitigation
3. Monitor critical path closely
4. Fast-track where possible"""
    
    def _allocate_resources(self, task_list: str) -> str:
        """
        Suggest resource allocation.
        
        Args:
            task_list: List of tasks
            
        Returns:
            Resource allocation recommendations
        """
        return """Resource Allocation Recommendations:

Team Composition:
- 2x Senior Developers
- 2x DevOps Engineers
- 1x Security Specialist
- 1x QA Engineer
- 1x Project Manager

Allocation by Phase:
- Assessment: Security + 1 DevOps
- Planning: Senior Developer + Project Manager
- Execution: Full team
- Testing: QA + Security

Optimization:
- Use parallel work streams
- Cross-train team members
- Plan for 80% capacity (buffer for meetings, etc.)
"""
    
    async def generate_project_charter(
        self,
        project_name: str,
        objective: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a complete project charter.
        
        Args:
            project_name: Name of the project
            objective: Project objective
            context: Additional context
            
        Returns:
            Project charter in markdown format
        """
        logger.info(f"Generating project charter for: {project_name}")
        
        prompt = f"""Generate a comprehensive project charter for:

Project Name: {project_name}
Objective: {objective}

Include all standard PMBOK sections:
1. Project Purpose
2. Objectives and Success Criteria
3. High-Level Requirements
4. Key Stakeholders
5. Assumptions and Constraints
6. High-Level Risks
7. Budget Estimate
8. Timeline
9. Authority and Approval

Format as professional markdown document."""
        
        charter = await self.chat(prompt)
        return charter
    
    async def generate_raci_matrix(
        self,
        tasks: List[Dict[str, Any]],
        stakeholders: List[str]
    ) -> Dict[str, Any]:
        """
        Generate RACI matrix for tasks and stakeholders.
        
        Args:
            tasks: List of task dictionaries
            stakeholders: List of stakeholder names
            
        Returns:
            RACI matrix as dictionary
        """
        logger.info("Generating RACI matrix")
        
        # In production, this would be more sophisticated
        raci_matrix = {
            "tasks": [],
            "stakeholders": stakeholders
        }
        
        for task in tasks:
            task_raci = {
                "task_id": task.get("id"),
                "task_name": task.get("name"),
                "assignments": {}
            }
            
            # Simple assignment logic (would be ML-based in production)
            for stakeholder in stakeholders:
                if "manager" in stakeholder.lower():
                    task_raci["assignments"][stakeholder] = "A"  # Accountable
                elif "lead" in stakeholder.lower():
                    task_raci["assignments"][stakeholder] = "R"  # Responsible
                else:
                    task_raci["assignments"][stakeholder] = "C"  # Consulted
            
            raci_matrix["tasks"].append(task_raci)
        
        return raci_matrix
