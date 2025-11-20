"""
A2A Server Setup Module
Sets up Google A2A protocol servers for agents
"""

import asyncio
import threading
import time
import uvicorn
import nest_asyncio
import os
from typing import Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

import config
import sys

# Workaround for google-adk==1.9.0 compatibility with a2a-sdk==0.3.0
try:
    from a2a.client import client as real_client_module
    from a2a.client.card_resolver import A2ACardResolver
    
    class PatchedClientModule:
        def __init__(self, real_module) -> None:
            for attr in dir(real_module):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(real_module, attr))
            self.A2ACardResolver = A2ACardResolver
    
    patched_module = PatchedClientModule(real_client_module)
    sys.modules['a2a.client.client'] = patched_module
except ImportError:
    pass  # If a2a-sdk not available, skip patching

nest_asyncio.apply()

# Store server tasks
server_tasks: list[asyncio.Task] = []
servers_started = False


def create_agent_a2a_server(agent, agent_card: AgentCard):
    """Create an A2A server for any ADK agent.
    
    Args:
        agent: The ADK agent instance
        agent_card: The A2A agent card
    
    Returns:
        A2AStarletteApplication instance
    """
    # Ensure API key and base URL are available in environment for Runner
    import config
    if config.USE_LITELLM_PROXY and config.LITELLM_BASE_URL:
        # Configure for LiteLLM proxy
        litellm_base = config.LITELLM_BASE_URL.rstrip('/')
        # Set multiple possible environment variable names
        os.environ['GOOGLE_GENAI_API_BASE'] = litellm_base
        os.environ['GEMINI_API_BASE'] = litellm_base
        api_key = config.LITELLM_API_KEY if config.LITELLM_API_KEY else (config.GOOGLE_API_KEY or config.GOOGLE_GENAI_API_KEY)
        if api_key:
            os.environ['GOOGLE_GENAI_API_KEY'] = api_key
            os.environ['GEMINI_API_KEY'] = api_key
            os.environ['GOOGLE_API_KEY'] = api_key
    elif not config.GOOGLE_GENAI_USE_VERTEXAI and config.GOOGLE_GENAI_API_KEY:
        # Direct Gemini API
        os.environ['GOOGLE_GENAI_API_KEY'] = config.GOOGLE_GENAI_API_KEY
        os.environ['GEMINI_API_KEY'] = config.GOOGLE_GENAI_API_KEY
    
    runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    
    executor_config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=executor_config)
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )


async def run_agent_server(agent, agent_card: AgentCard, port: int) -> None:
    """Run a single agent server."""
    app = create_agent_a2a_server(agent, agent_card)
    
    uvicorn_config = uvicorn.Config(
        app.build(),
        host=config.A2A_SERVER_HOST,
        port=port,
        log_level='warning',
        loop='none',
    )
    
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


def start_a2a_servers(customer_service_agent, database_agent, email_agent,
                      customer_service_card, database_card, email_card):
    """Start all A2A servers in background threads."""
    global servers_started
    
    if servers_started:
        return
    
    async def start_all_servers():
        """Start all servers in the same event loop."""
        tasks = [
            asyncio.create_task(
                run_agent_server(
                    customer_service_agent,
                    customer_service_card,
                    config.A2A_CUSTOMER_SERVICE_PORT
                )
            ),
            asyncio.create_task(
                run_agent_server(
                    database_agent,
                    database_card,
                    config.A2A_DATABASE_PORT
                )
            ),
            asyncio.create_task(
                run_agent_server(
                    email_agent,
                    email_card,
                    config.A2A_EMAIL_PORT
                )
            ),
        ]
        
        await asyncio.sleep(2)
        print('✅ All A2A agent servers started!')
        print(f'   - CustomerServiceAgent: http://{config.A2A_SERVER_HOST}:{config.A2A_CUSTOMER_SERVICE_PORT}')
        print(f'   - DatabaseAgent: http://{config.A2A_SERVER_HOST}:{config.A2A_DATABASE_PORT}')
        print(f'   - EmailAgent: http://{config.A2A_SERVER_HOST}:{config.A2A_EMAIL_PORT}')
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print('Shutting down servers...')
    
    def run_servers_in_background():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_all_servers())
    
    server_thread = threading.Thread(target=run_servers_in_background, daemon=True)
    server_thread.start()
    
    # Wait for servers to be ready
    time.sleep(3)
    servers_started = True

