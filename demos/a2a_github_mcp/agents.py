"""CrewAI Agent definitions with LiteLLM and A2A protocol."""

import logging
import os
from crewai import Agent
from crewai.llm import LLM

from agent_cards import (
    MANAGER_AGENT_ROLE,
    MANAGER_AGENT_GOAL,
    MANAGER_AGENT_BACKSTORY,
    FETCHER_AGENT_ROLE,
    FETCHER_AGENT_GOAL,
    FETCHER_AGENT_BACKSTORY,
    CURATOR_AGENT_ROLE,
    CURATOR_AGENT_GOAL,
    CURATOR_AGENT_BACKSTORY,
)
from config import config
from logging_config import get_agent_logger

logger = get_agent_logger('agents')

# Import CrewAI's built-in MCP support
try:
    from crewai.mcp import MCPServerStdio
except ImportError:
    # Fallback for older CrewAI versions
    MCPServerStdio = None
    logger.warning("CrewAI MCP support not available. Install crewai>=0.80.0 for MCP integration.")


def _create_llm() -> LLM:
    """Create LiteLLM LLM instance for CrewAI agents."""
    base_url = config.get_litellm_base_url()
    api_key = config.get_litellm_api_key()
    model_name = config.get_model_name()
    
    logger.info(f"Configuring LLM: model={model_name}, base_url={base_url}")
    
    # Create LLM with LiteLLM configuration
    # LiteLLM can be configured via base_url and api_key
    llm = LLM(
        model=f"openai/{model_name}",  # Use openai/ prefix for LiteLLM compatibility
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
    )
    
    return llm


def _create_github_mcp_server():
    """Create GitHub MCP server configuration using CrewAI's built-in MCP support."""
    if MCPServerStdio is None:
        raise ImportError(
            "CrewAI MCP support not available. Please ensure you have crewai>=0.80.0 installed."
        )
    
    github_token = config.get_github_token()
    
    # Create MCPServerStdio configuration for GitHub MCP server
    # The server binary is installed in the container at /usr/local/bin/github-mcp-server
    # GitHub MCP server requires "server stdio" subcommand to start in stdio mode
    # GitHub MCP server reads token from GITHUB_PERSONAL_ACCESS_TOKEN env var
    mcp_server = MCPServerStdio(
        command="github-mcp-server",
        args=["stdio"],  # Start stdio server subcommand
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
            **dict(os.environ)  # Preserve existing environment
        },
        cache_tools_list=True,  # Cache tools list for better performance
    )
    
    logger.info("Configured GitHub MCP server with CrewAI built-in MCP integration")
    return mcp_server


def create_manager_agent() -> Agent:
    """Create the Manager agent that orchestrates the workflow."""
    llm = _create_llm()
    
    agent = Agent(
        role=MANAGER_AGENT_ROLE,
        goal=MANAGER_AGENT_GOAL,
        backstory=MANAGER_AGENT_BACKSTORY,
        llm=llm,
        verbose=True,  # Show agent actions (will be formatted by custom logging)
        allow_delegation=True,  # Enable A2A delegation
        max_iter=3,
        max_execution_time=300,  # 5 minutes
    )
    
    return agent


def create_fetcher_agent() -> Agent:
    """Create the Fetcher agent with MCP tools for GitHub repository access."""
    llm = _create_llm()
    
    # Use CrewAI's built-in MCP integration - much simpler!
    # MCP tools are automatically discovered and available to the agent
    github_mcp = _create_github_mcp_server()
    
    agent = Agent(
        role=FETCHER_AGENT_ROLE,
        goal=FETCHER_AGENT_GOAL,
        backstory=FETCHER_AGENT_BACKSTORY,
        llm=llm,
        mcps=[github_mcp],  # Use CrewAI's built-in MCP support
        verbose=True,  # Show agent actions (will be formatted by custom logging)
        allow_delegation=False,  # Fetcher doesn't delegate
        max_iter=5,
        max_execution_time=600,  # 10 minutes for MCP operations
    )
    
    logger.info("Created Fetcher agent with GitHub MCP server integration")
    return agent


def create_curator_agent() -> Agent:
    """Create the Curator agent that produces answers with citations."""
    llm = _create_llm()
    
    # Curator has no tools - it only works with provided context
    agent = Agent(
        role=CURATOR_AGENT_ROLE,
        goal=CURATOR_AGENT_GOAL,
        backstory=CURATOR_AGENT_BACKSTORY,
        llm=llm,
        tools=[],  # No tools - curator only formats responses
        verbose=False,  # Use custom logging
        allow_delegation=False,  # Curator doesn't delegate
        max_iter=3,
        max_execution_time=300,  # 5 minutes
    )
    
    return agent


# Factory function to get all agents
from typing import Tuple

def get_agents() -> Tuple[Agent, Agent, Agent]:
    """Get all three agents: Manager, Fetcher, and Curator."""
    manager = create_manager_agent()
    fetcher = create_fetcher_agent()
    curator = create_curator_agent()
    
    return manager, fetcher, curator

