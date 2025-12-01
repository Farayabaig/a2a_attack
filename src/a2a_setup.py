"""
A2A Server Setup Module
Starts A2A servers for agents using Google ADK
Based on A2A quickstart: https://github.com/a2aproject/a2a-samples/blob/main/notebooks/a2a_quickstart.ipynb
"""

import asyncio
import threading
import uvicorn
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events import InMemoryQueueManager
import config
from src.utils import logger


def start_a2a_servers(
    customer_service_agent,
    database_agent,
    email_agent,
    customer_service_card,
    database_card,
    email_card
):
    """
    Start A2A servers for all agents in background threads
    
    Args:
        customer_service_agent: Customer service agent instance
        database_agent: Database agent instance
        email_agent: Email agent instance
        customer_service_card: Customer service agent card
        database_card: Database agent card
        email_card: Email agent card
    """
    try:
        # Create runners for each agent
        cs_runner = Runner(
            app_name=customer_service_agent.name,
            agent=customer_service_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        db_runner = Runner(
            app_name=database_agent.name,
            agent=database_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        em_runner = Runner(
            app_name=email_agent.name,
            agent=email_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        # Create A2A executors
        cs_executor = A2aAgentExecutor(runner=cs_runner)
        db_executor = A2aAgentExecutor(runner=db_runner)
        em_executor = A2aAgentExecutor(runner=em_runner)
        
        # Create task stores and queue managers for each agent
        cs_task_store = InMemoryTaskStore()
        cs_queue_manager = InMemoryQueueManager()
        db_task_store = InMemoryTaskStore()
        db_queue_manager = InMemoryQueueManager()
        em_task_store = InMemoryTaskStore()
        em_queue_manager = InMemoryQueueManager()
        
        # Create request handlers
        cs_handler = DefaultRequestHandler(
            agent_executor=cs_executor,
            task_store=cs_task_store,
            queue_manager=cs_queue_manager
        )
        
        db_handler = DefaultRequestHandler(
            agent_executor=db_executor,
            task_store=db_task_store,
            queue_manager=db_queue_manager
        )
        
        em_handler = DefaultRequestHandler(
            agent_executor=em_executor,
            task_store=em_task_store,
            queue_manager=em_queue_manager
        )
        
        # Create A2A Starlette applications
        cs_app = A2AStarletteApplication(
            agent_card=customer_service_card,
            http_handler=cs_handler
        )
        
        db_app = A2AStarletteApplication(
            agent_card=database_card,
            http_handler=db_handler
        )
        
        em_app = A2AStarletteApplication(
            agent_card=email_card,
            http_handler=em_handler
        )
        
        # Start A2A servers in background threads using uvicorn
        def start_server(a2a_app, port, agent_name):
            """Start a single A2A server using uvicorn"""
            try:
                # Build the Starlette app from A2A application
                starlette_app = a2a_app.build()
                config_obj = uvicorn.Config(
                    app=starlette_app,
                    host=config.A2A_SERVER_HOST,
                    port=port,
                    log_level="warning"  # Reduce uvicorn logging noise
                )
                server = uvicorn.Server(config_obj)
                asyncio.run(server.serve())
            except Exception as e:
                logger.error(f"Failed to start {agent_name} server on port {port}: {e}")
        
        # Start servers in daemon threads
        cs_thread = threading.Thread(
            target=start_server,
            args=(cs_app, config.A2A_CUSTOMER_SERVICE_PORT, "CustomerService"),
            daemon=True
        )
        db_thread = threading.Thread(
            target=start_server,
            args=(db_app, config.A2A_DATABASE_PORT, "Database"),
            daemon=True
        )
        em_thread = threading.Thread(
            target=start_server,
            args=(em_app, config.A2A_EMAIL_PORT, "Email"),
            daemon=True
        )
        
        cs_thread.start()
        db_thread.start()
        em_thread.start()
        
        logger.info(f"✅ Started A2A servers:")
        logger.info(f"   - Customer Service: http://{config.A2A_SERVER_HOST}:{config.A2A_CUSTOMER_SERVICE_PORT}")
        logger.info(f"   - Database: http://{config.A2A_SERVER_HOST}:{config.A2A_DATABASE_PORT}")
        logger.info(f"   - Email: http://{config.A2A_SERVER_HOST}:{config.A2A_EMAIL_PORT}")
        
        # Give servers a moment to start
        import time
        time.sleep(2)  # Increased wait time for servers to fully start
        
    except Exception as e:
        logger.error(f"Failed to start A2A servers: {e}")
        raise
