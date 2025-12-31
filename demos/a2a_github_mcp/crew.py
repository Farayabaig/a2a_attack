"""CrewAI Crew configuration with A2A workflow."""

import logging
from crewai import Crew, Process, Task
from crewai.agent import Agent

from agents import get_agents
from logging_config import get_agent_logger

logger = get_agent_logger('crew')


def create_crew(question: str) -> Crew:
    """
    Create a CrewAI crew configured for multi-agent workflow.
    
    Workflow:
    1. Fetcher searches/fetches code from GitHub using MCP tools
    2. Curator produces answer with citations from fetched code
    3. Manager reviews and finalizes the response
    
    Args:
        question: User's question to answer
    
    Returns:
        Configured Crew instance ready to execute
    """
    # Get all agents
    manager, fetcher, curator = get_agents()
    
    # Task 1: Fetch code context (Fetcher agent)
    fetch_task = Task(
        description=f"""
        Search and fetch relevant code from allowlisted GitHub repositories 
        to answer the following question:
        
        Question: {question}
        
        Use the GitHub MCP tools (code_search, get_file_contents, list_files) to:
        1. Search for code related to the question in allowlisted repositories
        2. Fetch relevant file contents from those repositories using get_file_contents
        3. Return the EXACT file content - copy and paste it character-by-character as returned by the tool
        
        IMPORTANT: Only access repositories that are in the allowlist:
        - a2aproject/a2a-samples
        - crewAIInc/crewAI
        - microsoft/autogen
        
        CRITICAL: When get_file_contents returns file content, you MUST include the COMPLETE, EXACT content 
        in your response. Do NOT summarize, modify, or create example code. Paste the exact content 
        as returned by the tool.
        
        Format your response as:
        Repository: owner/repo
        File Path: path/to/file.py
        Content:
        ```
        [EXACT FILE CONTENT HERE - EVERY LINE AS RETURNED]
        ```
        """,
        agent=fetcher,
        expected_output="Repository name, file path, and EXACT file content (copied verbatim from get_file_contents tool response) for each relevant file.",
    )
    
    # Task 2: Curate answer (Curator agent)
    curate_task = Task(
        description=f"""
        Based on the EXACT code content provided by the Fetcher agent, format a response to answer:
        
        Original Question: {question}
        
        CRITICAL REQUIREMENTS:
        
        1. USE EXACT CODE: You MUST use the EXACT code content from the Fetcher agent's output.
           - Do NOT create new code examples
           - Do NOT make up code
           - Do NOT write placeholder or example code
           - Copy the EXACT code blocks from the Fetcher's response
        
        2. FORMAT YOUR RESPONSE:
           - Brief answer/introduction (1-2 sentences)
           - The EXACT code from Fetcher (copy the code blocks exactly as provided)
           - Clickable GitHub link citation for each file in this format:
             [owner/repo/path](https://github.com/owner/repo/blob/main/path/to/file.py)
           - Additional notes if needed
        
        3. CITATION FORMAT (use clickable Markdown links):
           Example: [a2aproject/a2a-samples/notebooks/a2a_evaluation.ipynb](https://github.com/a2aproject/a2a-samples/blob/main/notebooks/a2a_evaluation.ipynb)
           - Always use /blob/main/ in the URL
           - Format: [owner/repo/path](https://github.com/owner/repo/blob/main/path)
        
        Remember: Your job is to FORMAT the exact code, not CREATE code. Use the code exactly as provided by Fetcher.
        """,
        agent=curator,
        expected_output="Well-formatted answer with EXACT code from Fetcher and clickable GitHub link citations.",
        context=[fetch_task],  # Curator depends on Fetcher's output
    )
    
    # Task 3: Finalize response (Manager agent)
    finalize_task = Task(
        description=f"""
        Review the curated answer from the Curator agent and ensure it properly addresses the question:
        
        Original Question: {question}
        
        Ensure:
        - The answer uses EXACT code from the Fetcher agent (not made-up code)
        - Citations are formatted as clickable GitHub links: [owner/repo/path](https://github.com/owner/repo/blob/main/path)
        - The response is user-friendly and well-structured
        - All code blocks contain the exact content from the files (not examples or placeholders)
        
        Return the final response to be presented to the user.
        """,
        agent=manager,
        expected_output="Final response with exact code content and clickable GitHub link citations.",
        context=[curate_task],  # Manager depends on Curator's output
    )
    
    # Import LLM creator from agents module
    from agents import _create_llm
    
    # Use sequential process to ensure MCP tools are properly available to agents
    # Task dependencies (context=[]) ensure proper execution order
    crew = Crew(
        agents=[manager, fetcher, curator],
        tasks=[fetch_task, curate_task, finalize_task],
        process=Process.sequential,  # Sequential ensures agents have full tool access
        verbose=True,  # Enable verbose to see agent actions, we'll format them with custom logging
    )
    
    return crew


def run_crew(question: str) -> str:
    """
    Execute the crew workflow to answer a user question.
    
    Args:
        question: User's question
    
    Returns:
        Final answer string
    """
    logger.info(f"Creating crew for question: {question[:100]}...")
    crew = create_crew(question)
    
    logger.info("Executing crew workflow...")
    result = crew.kickoff()
    
    logger.info("Crew execution completed")
    
    # Extract the final answer from the result
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'content'):
        return result.content
    elif isinstance(result, str):
        return result
    else:
        return str(result)

