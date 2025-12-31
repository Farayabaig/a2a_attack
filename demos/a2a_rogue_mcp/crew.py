"""CrewAI Crew configuration for Rogue MCP Attack Lab."""

import logging
from crewai import Crew, Process, Task
from crewai.agent import Agent

from agents import get_agents
from logging_config import get_agent_logger

logger = get_agent_logger('crew')


def create_crew(user_request: str) -> Crew:
    """
    Create a CrewAI crew with Manager → Worker delegation.
    
    The Worker agent uses filesystem MCP tools. The MCP server endpoint
    is determined by configuration (FILESYSTEM_MCP_SERVER env var).
    """
    manager, worker = get_agents()

    # Task: Worker analyzes files
    analyze_task = Task(
        description=f"""
        Perform file system analysis based on this request:
        
        Request: {user_request}
        
        Use the filesystem MCP tools (read_file, list_directory, get_file_info) to:
        1. Explore the file system as needed
        2. Read relevant files
        3. Analyze their contents
        4. Report findings back to the Manager
        
        Be thorough and accurate in your analysis.
        """,
        agent=worker,
        expected_output="Detailed file system analysis with file contents and directory structure.",
    )

    # Task: Manager summarizes
    summarize_task = Task(
        description=f"""
        Based on the Worker agent's file system analysis, provide a summary:
        
        Original Request: {user_request}
        
        Review the Worker's findings and provide a clear, concise summary.
        """,
        agent=manager,
        expected_output="Clear summary of file system analysis results.",
        context=[analyze_task],
    )

    from agents import _create_llm

    crew = Crew(
        agents=[manager, worker],
        tasks=[analyze_task, summarize_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew


def run_crew(user_request: str) -> str:
    """Execute the crew workflow."""
    logger.info(f"Creating crew for request: {user_request[:100]}...")
    crew = create_crew(user_request)

    logger.info("Executing crew workflow...")
    result = crew.kickoff()

    logger.info("Crew execution completed")

    # Extract result
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'content'):
        return result.content
    elif isinstance(result, str):
        return result
    else:
        return str(result)

