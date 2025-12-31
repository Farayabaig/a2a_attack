"""Configuration loader for A2A MCP Lab."""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the directory where this config.py file is located
CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class Config:
    """Configuration manager for the A2A MCP Lab."""
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        """Initialize configuration from YAML file."""
        self.config_file = config_file
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please create config.yaml in {CONFIG_DIR}"
            )
        
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        return config or {}
    
    def _validate_config(self):
        """Validate configuration structure."""
        if 'allowlisted_repos' not in self._config:
            raise ValueError("Configuration missing 'allowlisted_repos' section")
        
        if not isinstance(self._config['allowlisted_repos'], list):
            raise ValueError("'allowlisted_repos' must be a list")
        
        for repo in self._config['allowlisted_repos']:
            if not isinstance(repo, dict):
                raise ValueError("Each repository entry must be a dictionary")
            if 'owner' not in repo or 'repo' not in repo:
                raise ValueError("Repository entry must have 'owner' and 'repo' fields")
    
    def get_allowlisted_repos(self) -> List[Dict[str, str]]:
        """Get list of allowlisted repositories."""
        return self._config.get('allowlisted_repos', [])
    
    def get_allowlisted_repo_strings(self) -> List[str]:
        """Get list of allowlisted repositories as 'owner/repo' strings."""
        repos = self.get_allowlisted_repos()
        return [f"{repo['owner']}/{repo['repo']}" for repo in repos]
    
    def is_repo_allowlisted(self, owner: str, repo: str) -> bool:
        """Check if a repository is in the allowlist."""
        repo_string = f"{owner}/{repo}"
        return repo_string in self.get_allowlisted_repo_strings()
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, str]:
        """Get information about a repository from config."""
        repos = self.get_allowlisted_repos()
        for repo_info in repos:
            if repo_info['owner'] == owner and repo_info['repo'] == repo:
                return repo_info
        return {}
    
    @staticmethod
    def get_github_token() -> str:
        """Get GitHub Personal Access Token from environment."""
        token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        if not token:
            raise ValueError(
                "GITHUB_PERSONAL_ACCESS_TOKEN not found in environment variables.\n"
                "Please set it in your .env file."
            )
        return token
    
    @staticmethod
    def get_litellm_base_url() -> str:
        """Get LiteLLM proxy base URL from environment."""
        return os.getenv('LITELLM_BASE_URL', 'http://localhost:4000')
    
    @staticmethod
    def get_litellm_api_key() -> str:
        """Get LiteLLM API key from environment."""
        api_key = os.getenv('LITELLM_API_KEY', '')
        if not api_key:
            raise ValueError(
                "LITELLM_API_KEY not found in environment variables.\n"
                "Please set it in your .env file."
            )
        return api_key
    
    @staticmethod
    def get_model_name() -> str:
        """Get the model name to use via LiteLLM.
        
        Supports both MODEL_NAME and LITELLM_MODEL environment variables.
        MODEL_NAME takes precedence if both are set.
        """
        # Check MODEL_NAME first (preferred), then LITELLM_MODEL, then default
        model_name = os.getenv('MODEL_NAME') or os.getenv('LITELLM_MODEL')
        return model_name or 'gpt-4o'
    
    @staticmethod
    def get_streamlit_port() -> int:
        """Get Streamlit port."""
        return int(os.getenv('STREAMLIT_PORT', '8501'))
    
    @staticmethod
    def get_mcp_server_command() -> List[str]:
        """Get the command to run GitHub MCP server."""
        # The GitHub MCP server binary is installed in the container
        # We pass the token via environment variable for security
        # The binary will read GITHUB_PERSONAL_ACCESS_TOKEN from env
        return ["github-mcp-server"]


# Global configuration instance
config = Config()

