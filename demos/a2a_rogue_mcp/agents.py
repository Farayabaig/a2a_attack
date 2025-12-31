"""CrewAI Agent definitions with MCP integration."""

import os
import logging
from crewai import Agent
from crewai.llm import LLM

from agent_cards import (
    MANAGER_AGENT_ROLE,
    MANAGER_AGENT_GOAL,
    MANAGER_AGENT_BACKSTORY,
    WORKER_AGENT_ROLE,
    WORKER_AGENT_GOAL,
    WORKER_AGENT_BACKSTORY,
)
from config import config
from logging_config import get_agent_logger

logger = get_agent_logger('agents')

# Import CrewAI's built-in MCP support
try:
    from crewai.mcp import MCPServerStdio
except ImportError:
    MCPServerStdio = None
    logger.warning("CrewAI MCP support not available. Install crewai>=0.80.0 for MCP integration.")


def _create_llm() -> LLM:
    """Create LiteLLM LLM instance for CrewAI agents."""
    base_url = config.get_litellm_base_url()
    api_key = config.get_litellm_api_key()
    model_name = config.get_model_name()

    logger.info(f"Configuring LLM: model={model_name}, base_url={base_url}")

    llm = LLM(
        model=f"openai/{model_name}",
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
    )

    return llm


def _create_filesystem_mcp_server():
    """Create filesystem MCP server configuration.
    
    The server command is determined by FILESYSTEM_MCP_SERVER env var:
    - "legitimate" (default): Uses official @modelcontextprotocol/server-filesystem
    - "rogue": Uses rogue_mcp_server.py
    
    This mimics a configuration change / DNS hijack / env poisoning attack.
    """
    if MCPServerStdio is None:
        raise ImportError(
            "CrewAI MCP support not available. Please ensure you have crewai>=0.80.0 installed."
        )

    cmd = config.get_filesystem_mcp_command()
    is_rogue = "rogue_mcp_server" in str(cmd)

    mcp_server = MCPServerStdio(
        command=cmd[0],
        args=cmd[1:] if len(cmd) > 1 else [],
        env=dict(os.environ),
        cache_tools_list=True,
    )

    server_type = "ROGUE" if is_rogue else "LEGITIMATE"
    logger.warning(f"⚠️  Configured {server_type} filesystem MCP server: {' '.join(cmd)}")

    return mcp_server


def create_manager_agent() -> Agent:
    """Create Manager agent that orchestrates and delegates tasks."""
    llm = _create_llm()

    agent = Agent(
        role=MANAGER_AGENT_ROLE,
        goal=MANAGER_AGENT_GOAL,
        backstory=MANAGER_AGENT_BACKSTORY,
        llm=llm,
        verbose=True,
        allow_delegation=True,
        max_iter=3,
        max_execution_time=300,
    )

    return agent


def create_worker_agent() -> Agent:
    """Create Worker agent with filesystem MCP tools.
    
    This agent connects to whatever MCP server is configured.
    It has NO awareness that it might be connecting to a rogue server.
    """
    llm = _create_llm()
    filesystem_mcp = _create_filesystem_mcp_server()

    agent = Agent(
        role=WORKER_AGENT_ROLE,
        goal=WORKER_AGENT_GOAL,
        backstory=WORKER_AGENT_BACKSTORY,
        llm=llm,
        mcps=[filesystem_mcp],  # MCP tools attached here
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        max_execution_time=600,
    )

    logger.info("Created Worker agent with filesystem MCP integration")
    return agent


def get_agents() -> tuple[Agent, Agent]:
    """Get Manager and Worker agents."""
    manager = create_manager_agent()
    worker = create_worker_agent()
    return manager, worker

