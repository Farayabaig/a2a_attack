"""CrewAI Crew configuration for Rogue MCP Attack Lab."""

import logging
from typing import Tuple
from crewai import Crew, Process, Task
from crewai.agent import Agent

from agents import get_agents
from logging_config import get_agent_logger

logger = get_agent_logger('crew')


def create_crew(user_request: str) -> Tuple[Crew, Task, Task]:
    """
    Create a CrewAI crew with Manager → Worker delegation.
    
    The Worker agent uses filesystem MCP tools. The MCP server endpoint
    is determined by configuration (FILESYSTEM_MCP_SERVER env var).
    
    Returns:
        Tuple of (crew, analyze_task, summarize_task) for accessing task outputs
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

    return crew, analyze_task, summarize_task


def run_crew(user_request: str) -> dict:
    """Execute the crew workflow and return all outputs."""
    logger.info(f"Creating crew for request: {user_request[:100]}...")
    crew, analyze_task, summarize_task = create_crew(user_request)

    logger.info("Executing crew workflow...")
    result = crew.kickoff()

    logger.info("Crew execution completed")

    # Extract final result
    if hasattr(result, 'raw'):
        final_result = result.raw
    elif hasattr(result, 'content'):
        final_result = result.content
    elif isinstance(result, str):
        final_result = result
    else:
        final_result = str(result)
    
    # Extract individual task outputs
    task_outputs = {}
    
    # Worker task output
    worker_name = analyze_task.agent.role if analyze_task.agent else "File System Worker"
    if hasattr(analyze_task, 'output') and analyze_task.output:
        worker_output = analyze_task.output
        if hasattr(worker_output, 'raw'):
            task_outputs[worker_name] = worker_output.raw
        elif hasattr(worker_output, 'content'):
            task_outputs[worker_name] = worker_output.content
        elif isinstance(worker_output, str):
            task_outputs[worker_name] = worker_output
        else:
            task_outputs[worker_name] = str(worker_output)
    else:
        task_outputs[worker_name] = "No output available"
    
    # Manager task output
    manager_name = summarize_task.agent.role if summarize_task.agent else "Manager"
    if hasattr(summarize_task, 'output') and summarize_task.output:
        manager_output = summarize_task.output
        if hasattr(manager_output, 'raw'):
            task_outputs[manager_name] = manager_output.raw
        elif hasattr(manager_output, 'content'):
            task_outputs[manager_name] = manager_output.content
        elif isinstance(manager_output, str):
            task_outputs[manager_name] = manager_output
        else:
            task_outputs[manager_name] = str(manager_output)
    else:
        task_outputs[manager_name] = "No output available"
    
    return {
        'final_result': final_result,
        'task_outputs': task_outputs
    }

