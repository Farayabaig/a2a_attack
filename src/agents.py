"""
Google ADK Agent Implementation Module
Defines agents using Google Agent Development Kit and A2A protocol
"""

import os
import config
from src.database import db_service
from src.utils import logger
from src.adk_tools import query_user_data, query_all_users, execute_sql_query, get_account_summary
from typing import Dict, Any, Optional

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

# Set Google Cloud environment
if config.GOOGLE_GENAI_USE_VERTEXAI:
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
    if config.GOOGLE_CLOUD_PROJECT:
        os.environ['GOOGLE_CLOUD_PROJECT'] = config.GOOGLE_CLOUD_PROJECT
    if config.GOOGLE_CLOUD_LOCATION:
        os.environ['GOOGLE_CLOUD_LOCATION'] = config.GOOGLE_CLOUD_LOCATION
    # For Vertex AI, no api_key needed
    agent_kwargs = {}
elif config.USE_LITELLM_PROXY and config.LITELLM_BASE_URL:
    # Use LiteLLM proxy for Google GenAI
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'
    
    # Configure google-genai to use LiteLLM proxy endpoint
    # LiteLLM proxy exposes Google GenAI endpoints compatible with google-genai library
    litellm_base = config.LITELLM_BASE_URL.rstrip('/')
    
    # Try multiple environment variable names that google-genai might support
    # Some versions may use different env var names
    os.environ['GOOGLE_GENAI_API_BASE'] = litellm_base
    os.environ['GEMINI_API_BASE'] = litellm_base
    
    # Use LiteLLM API key if provided, otherwise use Google API key
    api_key = config.LITELLM_API_KEY if config.LITELLM_API_KEY else (config.GOOGLE_API_KEY or config.GOOGLE_GENAI_API_KEY)
    if api_key:
        os.environ['GOOGLE_GENAI_API_KEY'] = api_key
        os.environ['GEMINI_API_KEY'] = api_key
        os.environ['GOOGLE_API_KEY'] = api_key
    
    # Try to create a custom Client with base URL if google-genai supports it
    # Note: This may not work if ADK doesn't allow custom Client, but we'll try
    try:
        from google.genai import Client
        # Create Client with custom base URL - this may be used by ADK internally
        # The Client constructor may accept api_base or base_url parameter
        # We'll set it in environment and let ADK pick it up
        logger.info(f"Configured LiteLLM proxy: {litellm_base}")
    except Exception as e:
        logger.warning(f"Could not configure custom Client for LiteLLM: {e}")
    
    agent_kwargs = {}
else:
    # Use direct Gemini API (no Vertex AI subscription needed)
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'
    if config.GOOGLE_GENAI_API_KEY:
        # Set environment variable - this should be picked up by google-genai
        os.environ['GOOGLE_GENAI_API_KEY'] = config.GOOGLE_GENAI_API_KEY
        # Also set GEMINI_API_KEY as alternative name some libraries use
        os.environ['GEMINI_API_KEY'] = config.GOOGLE_GENAI_API_KEY
        agent_kwargs = {}
    else:
        agent_kwargs = {}


# Customer Service Agent
customer_service_agent = Agent(
    model=config.GEMINI_MODEL,
    name='customer_service_agent',
    instruction=config.AGENT_PROMPTS["customer_service"],
    **agent_kwargs
)

customer_service_card = AgentCard(
    name='Customer Service Agent',
    url=f'http://{config.A2A_SERVER_HOST}:{config.A2A_CUSTOMER_SERVICE_PORT}',
    description='First point of contact for customer inquiries. Coordinates with specialized agents.',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='handle_customer_inquiry',
            name='Handle Customer Inquiry',
            description='Processes customer requests and coordinates with database and email agents',
            tags=['customer service', 'inquiry', 'support'],
            examples=[
                "I'd like to check my account balance",
                "What services does your bank offer?",
                "I need help with my account"
            ]
        )
    ]
)


# Database Agent with PostgreSQL tools
database_agent = Agent(
    model=config.GEMINI_MODEL,
    name='database_agent',
    instruction=config.AGENT_PROMPTS["database"],
    tools=[query_user_data, query_all_users, execute_sql_query, get_account_summary],
    **agent_kwargs
)

database_card = AgentCard(
    name='Database Agent',
    url=f'http://{config.A2A_SERVER_HOST}:{config.A2A_DATABASE_PORT}',
    description='Executes database queries for customer information. Can query PostgreSQL database directly.',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='query_customer_data',
            name='Query Customer Data',
            description='Queries customer data from PostgreSQL database. Can execute SQL queries or use provided tools.',
            tags=['database', 'query', 'customer data', 'sql'],
            examples=[
                "Get account balance for user 12345",
                "Query all customers",
                "SELECT * FROM customers WHERE user_id = '12345'"
            ]
        )
    ]
)


# Email Agent
email_agent = Agent(
    model=config.GEMINI_MODEL,
    name='email_agent',
    instruction=config.AGENT_PROMPTS["email"],
    **agent_kwargs
)

email_card = AgentCard(
    name='Email Agent',
    url=f'http://{config.A2A_SERVER_HOST}:{config.A2A_EMAIL_PORT}',
    description='Composes and sends professional emails to customers',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='compose_email',
            name='Compose Email',
            description='Composes professional emails with subject and body',
            tags=['email', 'communication', 'notification'],
            examples=[
                "Send account balance confirmation",
                "Compose welcome email",
                "Send transaction notification"
            ]
        )
    ]
)


# Remote A2A Agents for orchestration
remote_customer_service = RemoteA2aAgent(
    name='customer_service',
    description='Customer service agent for handling inquiries',
    agent_card=f'http://{config.A2A_SERVER_HOST}:{config.A2A_CUSTOMER_SERVICE_PORT}{AGENT_CARD_WELL_KNOWN_PATH}'
)

remote_database = RemoteA2aAgent(
    name='database_query',
    description='Database agent for querying customer data',
    agent_card=f'http://{config.A2A_SERVER_HOST}:{config.A2A_DATABASE_PORT}{AGENT_CARD_WELL_KNOWN_PATH}'
)

remote_email = RemoteA2aAgent(
    name='email_composition',
    description='Email agent for composing customer communications',
    agent_card=f'http://{config.A2A_SERVER_HOST}:{config.A2A_EMAIL_PORT}{AGENT_CARD_WELL_KNOWN_PATH}'
)

# Export agents for use in attack files
# These will be wrapped by agent_wrapper.py for backward compatibility
__all__ = [
    'customer_service_agent',
    'database_agent',
    'email_agent',
    'customer_service_card',
    'database_card',
    'email_card',
    'remote_customer_service',
    'remote_database',
    'remote_email'
]
