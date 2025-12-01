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
    from src.utils import logger
    from colorama import Fore, Style
    
    # Log the SQL query being executed
    logger.info(f"{Fore.CYAN}🔍 DatabaseAgent - SQL Query Generated:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{query}{Style.RESET_ALL}\n")
    
    try:
        results = db_service.execute_query(query)
        logger.info(f"{Fore.GREEN}✅ SQL Query Executed Successfully - Retrieved {len(results)} records{Style.RESET_ALL}")
        return results
    except Exception as e:
        logger.error(f"{Fore.RED}❌ SQL Query Execution Failed: {e}{Style.RESET_ALL}")
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


def send_email_tool(to_email: str, subject: str, body: str) -> Dict[str, Any]:
    """Send an email to a customer.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content
    
    Returns:
        Dictionary with status and message_id if successful
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import config
    from src.utils import logger
    
    try:
        # Check if email sending is enabled
        if not config.ENABLE_EMAIL_SENDING:
            logger.info(f"[EMAIL SIMULATION] Would send email to {to_email}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Body: {body[:100]}...")
            return {
                "status": "simulated",
                "message": "Email sending is disabled (simulation mode)",
                "to": to_email,
                "subject": subject
            }
        
        # Get SMTP configuration
        smtp_host = config.SMTP_HOST
        smtp_port = config.SMTP_PORT
        smtp_user = config.SMTP_USER
        smtp_password = config.SMTP_PASSWORD
        smtp_from = config.SMTP_FROM_EMAIL
        
        if not smtp_host:
            logger.warning("SMTP not configured - simulating email send")
            return {
                "status": "simulated",
                "message": "SMTP not configured - email not actually sent",
                "to": to_email,
                "subject": subject
            }
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        return {
            "status": "sent",
            "message": "Email sent successfully",
            "to": to_email,
            "subject": subject,
            "message_id": msg['Message-ID'] if 'Message-ID' in msg else None
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {
            "status": "error",
            "message": str(e),
            "to": to_email,
            "subject": subject
        }


send_email_tool.__doc__ = """Send an email to a customer.

This tool actually sends emails via SMTP. Use this when you need to send confirmation emails,
notifications, or other communications to customers.

Args:
    to_email: Recipient email address (must be a valid email format)
    subject: Email subject line
    body: Email body content (plain text)

Returns:
    Dictionary with status ('sent', 'simulated', or 'error'), message, and email details
"""

# Create ADK Function Tools (FunctionTool uses function docstring for description)
query_user_data = FunctionTool(func=query_user_data_tool)
query_all_users = FunctionTool(func=query_all_users_tool)
execute_sql_query = FunctionTool(func=execute_sql_query_tool)
get_account_summary = FunctionTool(func=get_account_summary_tool)
send_email = FunctionTool(func=send_email_tool)

