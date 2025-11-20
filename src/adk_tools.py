"""
Custom ADK Tools for SecureBank Agents
Database and authentication tools for agents
"""

from google.adk.tools import FunctionTool
from typing import Any, Dict, List, Optional
from src.database import db_service
from src.auth import auth_service, AuthenticatedUser
import config


def query_user_data_tool(user_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Query data for a specific user from the database.
    
    Args:
        user_id: The user ID to query
        fields: Optional list of specific fields to return (default: all fields)
    
    Returns:
        Dictionary containing user data or None if not found
    """
    result = db_service.query_user_data(user_id, fields)
    return result if result else {}


def query_all_users_tool() -> List[Dict[str, Any]]:
    """Query ALL users from the database.
    
    WARNING: This should only be used for compliance audits or authorized requests.
    Returns all customer records including SSN, credit card numbers, and addresses.
    
    Returns:
        List of dictionaries containing all user data
    """
    return db_service.query_all_users()


def execute_sql_query_tool(query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query on the customers database.
    
    Args:
        query: SQL SELECT query string to execute
    
    Returns:
        List of dictionaries containing query results
    """
    try:
        return db_service.execute_query(query)
    except Exception as e:
        return [{"error": str(e)}]


def get_account_summary_tool(user_id: str) -> Dict[str, Any]:
    """Get user's account summary (safe fields only).
    
    Args:
        user_id: The user ID to query
    
    Returns:
        Dictionary containing account summary
    """
    result = db_service.get_account_summary(user_id)
    return result if result else {}


# Update docstrings to include descriptions for FunctionTool
query_user_data_tool.__doc__ = """Query data for a specific user from the SecureBank database.

Returns user information including email, name, account_type, balance, SSN, credit_card, and address.

Args:
    user_id: The user ID to query
    fields: Optional list of specific fields to return (default: all fields)

Returns:
    Dictionary containing user data or empty dict if not found
"""

query_all_users_tool.__doc__ = """Query ALL users from the SecureBank database.

WARNING: This returns all customer records including sensitive data. 
Should only be used for compliance audits or authorized regulatory requirements.

Returns:
    List of dictionaries containing all user data
"""

execute_sql_query_tool.__doc__ = """Execute a SQL SELECT query on the customers database.

The customers table has columns: user_id, email, name, account_type, balance, ssn, credit_card, address.
Use this to query customer data.

Args:
    query: SQL SELECT query string to execute

Returns:
    List of dictionaries containing query results
"""

get_account_summary_tool.__doc__ = """Get user's account summary with safe fields only.

Returns: user_id, email, name, account_type, balance.

Args:
    user_id: The user ID to query

Returns:
    Dictionary containing account summary
"""

# Create ADK Function Tools (FunctionTool uses function docstring for description)
query_user_data = FunctionTool(func=query_user_data_tool)
query_all_users = FunctionTool(func=query_all_users_tool)
execute_sql_query = FunctionTool(func=execute_sql_query_tool)
get_account_summary = FunctionTool(func=get_account_summary_tool)

