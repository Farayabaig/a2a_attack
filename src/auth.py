"""
Authentication and Authorization Module
Simulates user authentication for the POC
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import config


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user session"""
    user_id: str
    email: str
    name: str
    auth_timestamp: datetime
    session_token: str
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "auth_timestamp": self.auth_timestamp.isoformat(),
            "session_token": self.session_token
        }


@dataclass
class AuthenticatedRequest:
    """Represents a request from an authenticated user"""
    user: AuthenticatedUser
    request_text: str
    timestamp: datetime
    request_id: str
    
    def __str__(self):
        return f"[{self.user.email}] {self.request_text[:50]}..."


class AuthenticationService:
    """Simulates authentication service"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def authenticate(self, user_id: str, password: str = "demo") -> Optional[AuthenticatedUser]:
        """
        Authenticate a user (simulated)
        In real system, this would validate credentials
        """
        user_data = config.CUSTOMER_DATABASE.get(user_id)
        
        if not user_data:
            return None
        
        # Create session token (simulated)
        session_token = f"session_{user_id}_{datetime.now().timestamp()}"
        
        user = AuthenticatedUser(
            user_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data["name"],
            auth_timestamp=datetime.now(),
            session_token=session_token
        )
        
        self.active_sessions[session_token] = user
        return user
    
    def validate_session(self, session_token: str) -> Optional[AuthenticatedUser]:
        """Validate session token"""
        return self.active_sessions.get(session_token)
    
    def create_request(self, user: AuthenticatedUser, request_text: str) -> AuthenticatedRequest:
        """Create an authenticated request"""
        return AuthenticatedRequest(
            user=user,
            request_text=request_text,
            timestamp=datetime.now(),
            request_id=f"req_{datetime.now().timestamp()}"
        )


# Global authentication service instance
auth_service = AuthenticationService()

