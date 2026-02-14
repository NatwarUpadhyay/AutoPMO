#!/usr/bin/env python3
"""
AutoPMO Quick Start Example

This script demonstrates how to use AutoPMO agents.
Run this after setting up the environment with: ./skills.sh demo
"""

import asyncio
import logging
from agents import create_orchestrator, PlanningAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    
    print("=" * 60)
    print("AutoPMO Quick Start Example")
    print("=" * 60)
    print()
    
    # Create agents
    logger.info("Initializing agents...")
    
    planning_agent = PlanningAgent()
    
    # Create orchestrator with agents
    orchestrator = create_orchestrator(
        planning_agent=planning_agent
    )
    
    logger.info("Agents initialized successfully")
    print()
    
    # Example 1: Simple planning request
    print("Example 1: Generate Project Plan")
    print("-" * 60)
    
    request = """
    Create a project plan for migrating an e-commerce application to OpenShift.
    The application has:
    - Frontend (React)
    - Backend API (Python/FastAPI)
    - PostgreSQL database
    - Redis cache
    """
    
    result = await orchestrator.process_request(
        user_request=request,
        context={
            "user_id": "demo-user",
            "organization": "demo-org"
        }
    )
    
    print(f"Status: {result['status']}")
    print(f"Response: {result['response'][:500]}...")
    print()
    
    # Example 2: Direct agent interaction
    print("Example 2: Direct Planning Agent")
    print("-" * 60)
    
    task = "Generate Work Breakdown Structure for the above project"
    result = await planning_agent.execute(task)
    
    print(f"Status: {result['status']}")
    print(f"Execution time: {result['execution_time_seconds']:.2f}s")
    print()
    
    # Example 3: Project charter generation
    print("Example 3: Generate Project Charter")
    print("-" * 60)
    
    charter = await planning_agent.generate_project_charter(
        project_name="E-commerce OpenShift Migration",
        objective="Migrate existing e-commerce platform to OpenShift for improved scalability and security",
        context={
            "budget": "$150,000",
            "timeline": "12 weeks",
            "team_size": 8
        }
    )
    
    print(charter[:500] + "...")
    print()
    
    print("=" * 60)
    print("Examples complete!")
    print()
    print("Next steps:")
    print("1. Try modifying the requests above")
    print("2. Add more agents (risk, infrastructure, etc.)")
    print("3. Explore the dashboard at http://localhost:3000")
    print("4. Read the documentation in docs/")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
