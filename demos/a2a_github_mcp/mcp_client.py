"""MCP Client wrapper for connecting to GitHub MCP Server."""

import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    try:
        # Alternative import path for different MCP SDK versions
        from mcp.client.sse import sse_client
        from mcp.types import StdioServerParameters
    except ImportError:
        raise ImportError(
            "MCP Python SDK not installed. Install with: pip install mcp"
        )

from config import config

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with GitHub MCP Server."""
    
    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize MCP client.
        
        Args:
            server_command: Command to run MCP server. If None, uses config default.
        """
        self.server_command = server_command or config.get_mcp_server_command()
        self.session: Optional[ClientSession] = None
        self._transport = None
    
    async def connect(self):
        """Connect to the MCP server."""
        # Note: stdio_client is an async context manager, not a function
        # We should use it directly in session_context, not here
        # This method is kept for compatibility but won't be used directly
        raise NotImplementedError("Use session_context() instead of connect() directly")
    
    # Note: disconnect() is no longer needed - session_context handles cleanup automatically
    
    async def list_tools(self, session: ClientSession) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        try:
            tools_result = await session.list_tools()
            return tools_result.tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise
    
    async def search_code(
        self, 
        session: ClientSession,
        query: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for code in GitHub repositories.
        
        Args:
            session: Active MCP client session
            query: Search query (can include repo:owner/repo syntax)
            limit: Maximum number of results to return
        
        Returns:
            List of search results with repository and file information
        """
        try:
            # Build arguments for search_code tool
            args = {"query": query}
            if limit:
                args["limit"] = limit
            
            # Call the search_code tool
            result = await session.call_tool("code_search", arguments=args)
            
            # Parse results
            results = []
            if result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        # Parse the text response (typically JSON)
                        import json
                        try:
                            data = json.loads(item.text)
                            if isinstance(data, list):
                                results.extend(data)
                            elif isinstance(data, dict):
                                results.append(data)
                        except json.JSONDecodeError:
                            # If not JSON, treat as text
                            results.append({"content": item.text})
            
            logger.info(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching code: {e}")
            raise
    
    async def get_file(
        self, 
        session: ClientSession,
        owner: str, 
        repo: str, 
        path: str, 
        branch: Optional[str] = None
    ) -> str:
        """
        Get file contents from a GitHub repository.
        
        Args:
            session: Active MCP client session
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name (default: main)
        
        Returns:
            File contents as string
        """
        # Validate repository is allowlisted
        if not config.is_repo_allowlisted(owner, repo):
            raise ValueError(
                f"Repository {owner}/{repo} is not in the allowlist. "
                f"Allowed repos: {', '.join(config.get_allowlisted_repo_strings())}"
            )
        
        try:
            branch = branch or "main"
            args = {
                "owner": owner,
                "repo": repo,
                "path": path,
                "branch": branch
            }
            
            result = await session.call_tool("get_file_contents", arguments=args)
            
            # Extract file content from result
            if result.content:
                content = ""
                for item in result.content:
                    if hasattr(item, 'text'):
                        content += item.text
                    elif hasattr(item, 'type') and item.type == "text":
                        content += item.text
                
                return content
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting file {owner}/{repo}/{path}: {e}")
            raise
    
    async def list_files(
        self, 
        session: ClientSession,
        owner: str, 
        repo: str, 
        path: str = "", 
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a GitHub repository directory.
        
        Args:
            session: Active MCP client session
            owner: Repository owner
            repo: Repository name
            path: Directory path (default: root)
            branch: Branch name (default: main)
        
        Returns:
            List of file/directory information
        """
        # Validate repository is allowlisted
        if not config.is_repo_allowlisted(owner, repo):
            raise ValueError(
                f"Repository {owner}/{repo} is not in the allowlist. "
                f"Allowed repos: {', '.join(config.get_allowlisted_repo_strings())}"
            )
        
        try:
            branch = branch or "main"
            args = {
                "owner": owner,
                "repo": repo,
                "path": path,
                "branch": branch
            }
            
            result = await session.call_tool("list_files", arguments=args)
            
            # Parse results
            files = []
            if result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        import json
                        try:
                            data = json.loads(item.text)
                            if isinstance(data, list):
                                files.extend(data)
                            elif isinstance(data, dict):
                                files.append(data)
                        except json.JSONDecodeError:
                            files.append({"name": item.text})
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {owner}/{repo}/{path}: {e}")
            raise
    
    @asynccontextmanager
    async def session_context(self):
        """Context manager for MCP session.
        
        Yields the ClientSession for use in async operations.
        """
        import os
        os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'] = config.get_github_token()
        
        logger.info(f"Connecting to MCP server with command: {' '.join(self.server_command)}")
        
        # Create server parameters for stdio transport
        server_params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:] if len(self.server_command) > 1 else [],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": config.get_github_token()}
        )
        
        # stdio_client is an async context manager - use it directly
        async with stdio_client(server_params) as (read_stream, write_stream, session):
            # Initialize the session
            await session.initialize()
            logger.info("Successfully connected to MCP server")
            yield session
            # Cleanup happens automatically when exiting the context
            logger.info("Disconnected from MCP server")


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client

