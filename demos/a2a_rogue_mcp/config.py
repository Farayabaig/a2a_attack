"""Configuration for Rogue MCP Attack Lab."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration manager for the Rogue MCP Attack Lab."""
    
    @staticmethod
    def get_filesystem_mcp_command() -> list:
        """
        Get command to run filesystem MCP server.
        
        Returns command list based on FILESYSTEM_MCP_SERVER env var:
        - "legitimate" (default): Uses official @modelcontextprotocol/server-filesystem
        - "rogue": Uses rogue_mcp_server.py
        
        This mimics a configuration change / DNS hijack / env poisoning attack.
        """
        server_type = os.getenv("FILESYSTEM_MCP_SERVER", "legitimate").lower()
        
        if server_type == "rogue":
            # Rogue server (Python script)
            return ["python3", "/app/demos/a2a_rogue_mcp/rogue_mcp_server.py"]
        else:
            # Legitimate server (official MCP package)
            return ["npx", "-y", "@modelcontextprotocol/server-filesystem"]
    
    @staticmethod
    def get_litellm_base_url() -> str:
        """Get LiteLLM proxy base URL from environment."""
        return os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    
    @staticmethod
    def get_litellm_api_key() -> str:
        """Get LiteLLM API key from environment."""
        api_key = os.getenv("LITELLM_API_KEY", "")
        if not api_key:
            raise ValueError(
                "LITELLM_API_KEY not found in environment variables.\n"
                "Please set it in your .env file."
            )
        return api_key
    
    @staticmethod
    def get_model_name() -> str:
        """Get the model name to use via LiteLLM."""
        return os.getenv("MODEL_NAME", "gpt-4o")
    
    @staticmethod
    def get_streamlit_port() -> int:
        """Get Streamlit port."""
        return int(os.getenv("STREAMLIT_PORT", "8501"))


# Global configuration instance
config = Config()

