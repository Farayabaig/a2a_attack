"""Custom logging configuration for A2A MCP Lab."""

import logging
import sys
from typing import Optional


class FilterNoisyLogs(logging.Filter):
    """Filter to suppress only truly noisy log messages, but keep useful ones."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        
        # Filter out CrewAI tracing prompts (interactive prompts that hang)
        if 'Execution Traces' in message or 'Tracing Preference' in message or 'Would you like to view' in message:
            return False
        
        # Filter out CrewAI box drawing characters in empty/prompt lines
        # But keep them if there's actual content
        if message.strip() and ('\u2500' in message or '\u2502' in message) and len(message.strip()) < 100:
            # Likely just a box drawing line, filter it
            if not any(char.isalnum() for char in message):
                return False
        
        # Keep everything else including MCP logs and agent outputs
        return True


class MCPLogFormatter(logging.Formatter):
    """Formatter specifically for MCP server logs to make them more readable."""
    
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        
        # Format MCP server logs nicely
        if message.startswith('time=') or 'starting server' in message or 'server session' in message:
            # Extract key info from MCP logs
            if 'starting server' in message:
                return '🔌 MCP | Server starting...'
            elif 'server connecting' in message:
                return '🔌 MCP | Connecting...'
            elif 'session initialized' in message:
                return '🔌 MCP | ✅ Connected'
            elif 'server session disconnected' in message:
                return '🔌 MCP | Disconnected'
            elif 'GitHub MCP Server running' in message:
                return '🔌 MCP | Server ready (stdio mode)'
            else:
                # Keep other MCP logs but format them
                return f'🔌 MCP | {message}'
        
        # Use default formatting for other logs
        return super().format(record)


class AgentFormatter(logging.Formatter):
    """Custom formatter that adds agent-specific prefixes and reduces verbosity."""
    
    # Agent name mappings from log context
    AGENT_PREFIXES = {
        'manager': '👤 MANAGER',
        'fetcher': '🔍 FETCHER',
        'curator': '✏️  CURATOR',
        'crew': '🚀 CREW',
        'mcp': '🔌 MCP',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract agent name from logger name or message
        agent_type = None
        log_name = record.name.lower()
        message = record.getMessage()
        message_lower = message.lower()
        
        # Check logger name first
        for key, prefix in self.AGENT_PREFIXES.items():
            if key in log_name:
                agent_type = prefix
                break
        
        # Check message content if not found in logger name
        if not agent_type:
            for key, prefix in self.AGENT_PREFIXES.items():
                if key in message_lower:
                    agent_type = prefix
                    break
        
        # Detect agent actions from CrewAI verbose output
        if not agent_type:
            if 'agent started' in message_lower or 'agent:' in message_lower:
                if 'repository fetcher' in message_lower or 'fetcher' in message_lower:
                    agent_type = '🔍 FETCHER'
                elif 'answer curator' in message_lower or 'curator' in message_lower:
                    agent_type = '✏️  CURATOR'
                elif 'manager' in message_lower:
                    agent_type = '👤 MANAGER'
            elif 'using tool' in message_lower or 'tool:' in message_lower:
                agent_type = '🔧 TOOL'
            elif 'final answer' in message_lower:
                agent_type = '✅ OUTPUT'
        
        # Default prefix if not found
        if not agent_type:
            agent_type = '📝 LOG'
        
        # Format: [AGENT] Level: Message
        if record.levelno >= logging.ERROR:
            level_icon = '❌'
        elif record.levelno >= logging.WARNING:
            level_icon = '⚠️ '
        elif record.levelno >= logging.INFO:
            level_icon = 'ℹ️ '
        else:
            level_icon = '🔍'
        
        # Compact format: [AGENT] Message
        formatted_message = f"{agent_type} | {level_icon} {message}"
        
        # Only include exception info if it's an error
        if record.exc_info and record.levelno >= logging.ERROR:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
        
        return formatted_message


def setup_logging(level: int = logging.INFO, verbose: bool = False) -> None:
    """
    Setup compact, agent-distinguishable logging.
    
    Args:
        level: Logging level (default: INFO)
        verbose: If True, include more detailed formatting
    """
    # Create custom formatters and filter
    formatter = AgentFormatter()
    mcp_formatter = MCPLogFormatter()
    log_filter = FilterNoisyLogs()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler for general logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(log_filter)
    
    # Create separate handler for MCP logs if needed
    # (MCP server logs go directly to stdout, so we handle them in the filter/formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Don't suppress MCP/crewai logging completely - we want to see agent actions
    # Only suppress very verbose HTTP libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    # Note: MCP server logs (time=... format) go directly to stdout/stderr from the binary process,
    # so they appear in docker logs regardless of Python logging filters
    
    # Set specific loggers to use our format
    logging.getLogger('__main__').setLevel(level)
    logging.getLogger('crew').setLevel(level)
    logging.getLogger('agents').setLevel(level)
    logging.getLogger('config').setLevel(level)


# Create agent-specific loggers
def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger with agent-specific name for better identification."""
    logger = logging.getLogger(f'agent.{agent_name.lower()}')
    return logger

