"""
A2A Client for communicating with A2A agents
"""

import asyncio
import httpx
from typing import Any, Optional
from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.types import AgentCard, TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from src.utils import logger


class A2AClient:
    """Simple A2A client for calling A2A servers"""
    
    def __init__(self, default_timeout: float = 240.0):
        self._agent_info_cache: dict[str, dict[str, Any] | None] = {}
        self.default_timeout = default_timeout
    
    async def send_message(self, agent_url: str, message: str) -> str:
        """Send a message to an A2A agent and get response.
        
        Args:
            agent_url: Base URL of the A2A agent server
            message: Text message to send
        
        Returns:
            Response text from the agent
        """
        timeout_config = httpx.Timeout(
            timeout=self.default_timeout,
            connect=10.0,
            read=self.default_timeout,
            write=10.0,
            pool=5.0,
        )
        
        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            # Fetch or use cached agent card
            if agent_url in self._agent_info_cache and self._agent_info_cache[agent_url] is not None:
                agent_card_data = self._agent_info_cache[agent_url]
            else:
                agent_card_response = await httpx_client.get(
                    f'{agent_url}{AGENT_CARD_WELL_KNOWN_PATH}'
                )
                agent_card_data = self._agent_info_cache[agent_url] = agent_card_response.json()
            
            agent_card = AgentCard(**agent_card_data)
            
            config = ClientConfig(
                httpx_client=httpx_client,
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                use_client_preference=True,
            )
            
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            message_obj = create_text_message_object(content=message)
            
            responses = []
            async for response in client.send_message(message_obj):
                responses.append(response)
            
            # Parse response - handle different response formats
            if not responses:
                return 'No response received'
            
            # Try to extract text from response
            for response in responses:
                if isinstance(response, tuple) and len(response) > 0:
                    task = response[0]
                    try:
                        # Try to get text from artifacts
                        if hasattr(task, 'artifacts') and task.artifacts:
                            if len(task.artifacts) > 0:
                                artifact = task.artifacts[0]
                                if hasattr(artifact, 'parts') and artifact.parts:
                                    if len(artifact.parts) > 0:
                                        part = artifact.parts[0]
                                        if hasattr(part, 'root') and part.root:
                                            if hasattr(part.root, 'text'):
                                                return part.root.text
                        # Fallback: try to get text directly
                        if hasattr(task, 'text'):
                            return task.text
                        # Last resort: string representation
                        return str(task)
                    except (AttributeError, IndexError, TypeError) as e:
                        logger.warning(f"Error parsing response: {e}")
                        continue
                elif hasattr(response, 'text'):
                    return response.text
                elif isinstance(response, str):
                    return response
            
            # If we get here, return string representation of first response
            return str(responses[0]) if responses else 'No response received'
    
    def send_message_sync(self, agent_url: str, message: str) -> str:
        """Synchronous wrapper for send_message."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_message(agent_url, message))


# Global A2A client instance
a2a_client = A2AClient()

