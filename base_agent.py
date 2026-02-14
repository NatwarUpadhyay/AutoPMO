"""
Base Agent Class for AutoPMO

This module provides the base class that all specialized agents inherit from.
It handles common functionality like LLM communication, logging, and error handling.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain_community.chat_models import ChatOpenAI

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all AutoPMO agents.
    
    Attributes:
        name: Agent identifier
        description: What this agent does
        llm: Language model instance
        tools: List of tools available to this agent
        memory: Conversation memory
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_base_url: str = "http://llm-server:8000/v1",
        llm_model: str = "mistral-7b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name
            description: Agent description
            llm_base_url: URL for LLM API
            llm_model: Model identifier
            temperature: LLM temperature (0-1)
            max_tokens: Maximum tokens in response
        """
        self.name = name
        self.description = description
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            base_url=llm_base_url,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key="not-needed"  # For local/OpenShift deployments
        )
        
        # Tools registry
        self.tools: List[Tool] = []
        
        # Execution history
        self.history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Must be implemented by subclasses.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def register_tools(self) -> List[Tool]:
        """
        Register tools specific to this agent.
        Must be implemented by subclasses.
        
        Returns:
            List of LangChain tools
        """
        pass
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: Task description in natural language
            context: Additional context (project_id, user_id, etc.)
            
        Returns:
            Result dictionary with status, data, and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"{self.name} executing task: {task[:100]}...")
            
            # Register tools if not already done
            if not self.tools:
                self.tools = self.register_tools()
            
            # Prepare context
            context = context or {}
            context_str = json.dumps(context, indent=2)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", f"Context:\n{context_str}\n\nTask:\n{task}")
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Execute
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True
            )
            
            result = await executor.ainvoke({
                "input": task,
                "context": context_str
            })
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Format response
            response = {
                "status": "success",
                "agent": self.name,
                "task": task,
                "result": result.get("output", ""),
                "execution_time_seconds": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context
            }
            
            # Store in history
            self.history.append(response)
            
            logger.info(f"{self.name} completed task in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}", exc_info=True)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "error",
                "agent": self.name,
                "task": task,
                "error": str(e),
                "execution_time_seconds": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context
            }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get agent execution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of execution records
        """
        return self.history[-limit:]
    
    def clear_history(self):
        """Clear execution history."""
        self.history = []
        logger.info(f"{self.name} history cleared")
    
    async def chat(self, message: str) -> str:
        """
        Simple chat interface for testing.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=message)
        ]
        
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    def __repr__(self) -> str:
        return f"<{self.name} Agent: {self.description}>"
