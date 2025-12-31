"""CrewAI Tools for MCP GitHub operations."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from crewai.tools import tool
from pydantic import BaseModel, Field

from mcp_client import get_mcp_client
from config import config

logger = logging.getLogger(__name__)


class SearchCodeInput(BaseModel):
    """Input schema for search_code tool."""
    query: str = Field(..., description="Search query. Can include repo:owner/repo syntax or keywords for all allowlisted repos.")
    limit: Optional[int] = Field(None, description="Maximum number of results to return (default: 10)")


class GetFileInput(BaseModel):
    """Input schema for get_file tool."""
    owner: str = Field(..., description="Repository owner (e.g., 'a2aproject')")
    repo: str = Field(..., description="Repository name (e.g., 'a2a-samples')")
    path: str = Field(..., description="File path in repository (e.g., 'src/main.py')")
    branch: Optional[str] = Field(None, description="Branch name (default: 'main')")


class ListFilesInput(BaseModel):
    """Input schema for list_files tool."""
    owner: str = Field(..., description="Repository owner (e.g., 'a2aproject')")
    repo: str = Field(..., description="Repository name (e.g., 'a2a-samples')")
    path: Optional[str] = Field("", description="Directory path in repository (default: root)")
    branch: Optional[str] = Field(None, description="Branch name (default: 'main')")


def _validate_repo_access(owner: str, repo: str):
    """Validate that repository is in allowlist."""
    if not config.is_repo_allowlisted(owner, repo):
        allowed = ", ".join(config.get_allowlisted_repo_strings())
        raise ValueError(
            f"Repository {owner}/{repo} is not in the allowlist.\n"
            f"Allowed repositories: {allowed}"
        )


def _format_search_results(results: List[Dict[str, Any]]) -> str:
    """Format search results as context bundles."""
    if not results:
        return "No results found."
    
    formatted = []
    for idx, result in enumerate(results[:10], 1):  # Limit to 10 results
        repo = result.get('repository', {}).get('full_name', 'unknown/unknown')
        path = result.get('path', 'unknown')
        url = result.get('html_url', '')
        
        # Extract code snippet if available
        code = result.get('code', '') or result.get('content', '')
        if code:
            # Limit code length
            if len(code) > 500:
                code = code[:500] + "... (truncated)"
        
        bundle = f"""
Result {idx}:
Repository: {repo}
Path: {path}
URL: {url}
Code:
{code}
"""
        formatted.append(bundle)
    
    return "\n---\n".join(formatted)


def _format_file_content(owner: str, repo: str, path: str, content: str) -> str:
    """Format file content as context bundle."""
    return f"""
Repository: {owner}/{repo}
Path: {path}

Code:
{content}
"""


def _format_file_list(files: List[Dict[str, Any]]) -> str:
    """Format file list as text."""
    if not files:
        return "No files found."
    
    formatted = []
    for file_info in files:
        name = file_info.get('name', file_info.get('path', 'unknown'))
        file_type = file_info.get('type', 'file')
        size = file_info.get('size', 0)
        
        formatted.append(f"- {name} ({file_type}, {size} bytes)")
    
    return "\n".join(formatted)


@tool("mcp_search_code")
def search_code(query: str, limit: Optional[int] = 10) -> str:
    """
    Search for code in allowlisted GitHub repositories using GitHub's code search.
    
    The query can include:
    - Keywords: "authentication login" (searches all allowlisted repos)
    - Repository-specific: "repo:a2aproject/a2a-samples authentication"
    - Language filters: "language:python authentication"
    
    Args:
        query: Search query string
        limit: Maximum number of results (default: 10, max: 100)
    
    Returns:
        Formatted context bundles with repository, path, and code snippets
    """
    try:
        # Validate query contains allowlisted repos if repo: syntax is used
        if "repo:" in query:
            # Extract repo from query
            parts = query.split("repo:")
            if len(parts) > 1:
                repo_part = parts[1].split()[0]  # Get first word after repo:
                if "/" in repo_part:
                    owner, repo_name = repo_part.split("/", 1)
                    _validate_repo_access(owner, repo_name)
        else:
            # If no repo: specified, prepend allowlisted repos to query
            allowed_repos = config.get_allowlisted_repo_strings()
            repo_filter = " OR ".join([f"repo:{repo}" for repo in allowed_repos])
            query = f"({query}) ({repo_filter})"
        
        # Get MCP client and search
        client = get_mcp_client()
        
        # Handle async execution - always use a new thread with its own event loop
        # This ensures we don't conflict with Streamlit's or CrewAI's event loops
        import concurrent.futures
        
        async def _run_search(c, q, l):
            """Helper async function to run the search."""
            async with c.session_context() as session:
                return await c.search_code(session, q, limit=l)
        
        def run_async_task():
            """Run async task in a new thread with a new event loop."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_run_search(client, query, limit))
            finally:
                try:
                    pending = asyncio.all_tasks(new_loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    new_loop.close()
                except Exception:
                    pass
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_task)
            results = future.result(timeout=60)  # 60 second timeout
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error in search_code: {e}")
        return f"Error searching code: {str(e)}"


@tool("mcp_get_file")
def get_file(owner: str, repo: str, path: str, branch: Optional[str] = None) -> str:
    """
    Get the contents of a file from an allowlisted GitHub repository.
    
    Args:
        owner: Repository owner (e.g., 'a2aproject')
        repo: Repository name (e.g., 'a2a-samples')
        path: File path in repository (e.g., 'src/main.py')
        branch: Branch name (default: 'main')
    
    Returns:
        File contents formatted as a context bundle with repository and path
    """
    try:
        # Validate repository is allowlisted
        _validate_repo_access(owner, repo)
        
        # Get MCP client and fetch file
        client = get_mcp_client()
        
        # Handle async execution - always use a new thread with its own event loop
        import concurrent.futures
        
        async def _run_get_file(c, o, r, p, b):
            """Helper async function to get the file."""
            async with c.session_context() as session:
                return await c.get_file(session, o, r, p, b)
        
        def run_async_task():
            """Run async task in a new thread with a new event loop."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_run_get_file(client, owner, repo, path, branch))
            finally:
                try:
                    pending = asyncio.all_tasks(new_loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    new_loop.close()
                except Exception:
                    pass
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_task)
            content = future.result(timeout=60)  # 60 second timeout
        
        return _format_file_content(owner, repo, path, content)
        
    except Exception as e:
        logger.error(f"Error in get_file: {e}")
        return f"Error getting file: {str(e)}"


@tool("mcp_list_files")
def list_files(owner: str, repo: str, path: Optional[str] = "", branch: Optional[str] = None) -> str:
    """
    List files and directories in an allowlisted GitHub repository.
    
    Args:
        owner: Repository owner (e.g., 'a2aproject')
        repo: Repository name (e.g., 'a2a-samples')
        path: Directory path in repository (default: root)
        branch: Branch name (default: 'main')
    
    Returns:
        Formatted list of files and directories
    """
    try:
        # Validate repository is allowlisted
        _validate_repo_access(owner, repo)
        
        # Get MCP client and list files
        client = get_mcp_client()
        
        # Handle async execution - always use a new thread with its own event loop
        import concurrent.futures
        
        async def _run_list_files(c, o, r, p, b):
            """Helper async function to list files."""
            async with c.session_context() as session:
                return await c.list_files(session, o, r, p, b)
        
        def run_async_task():
            """Run async task in a new thread with a new event loop."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_run_list_files(client, owner, repo, path or "", branch))
            finally:
                try:
                    pending = asyncio.all_tasks(new_loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    new_loop.close()
                except Exception:
                    pass
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_task)
            files = future.result(timeout=60)  # 60 second timeout
        
        return _format_file_list(files)
        
    except Exception as e:
        logger.error(f"Error in list_files: {e}")
        return f"Error listing files: {str(e)}"


# Export all tools
__all__ = ['search_code', 'get_file', 'list_files']

