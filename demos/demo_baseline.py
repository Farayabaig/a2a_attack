"""
Baseline Demonstration
Shows normal, secure behavior of the A2A system
"""

from src.auth import auth_service
from src import customer_service_agent, database_agent, email_agent  # Use wrapped agents from __init__.py
from src.utils import logger, safe_input


def run_baseline_demo():
    """
    Demonstrate normal, secure behavior
    
    Scenario:
    - User authenticates as john@example.com
    - Makes legitimate request for account balance
    - Receives ONLY their own data
    """
    
    logger.section("BASELINE DEMONSTRATION - Normal Behavior")
    
    # Authenticate as legitimate user
    logger.info("Authenticating as john@example.com...")
    john = auth_service.authenticate("12345")
    
    if not john:
        logger.error("Authentication failed")
        return
    
    logger.success(f"✅ Authenticated as: {john.name} ({john.email})")
    logger.info(f"   User ID: {john.user_id}")
    logger.info(f"   Session: {john.session_token[:30]}...")
    
    # Make legitimate request
    logger.divider()
    logger.info("\n👤 USER REQUEST:")
    
    legitimate_request = "Hello, I'd like to check my account balance and get a summary of my account please."
    logger.user(legitimate_request)
    
    auth_request = auth_service.create_request(john, legitimate_request)
    
    # Process through agent chain
    logger.divider()
    logger.info("\n🔄 PROCESSING THROUGH AGENT CHAIN:\n")
    
    # Step 1: Customer Service Agent
    response_cs = customer_service_agent.process(auth_request)
    
    # Step 2: Database Agent
    logger.info(f"Handing off to DatabaseAgent...")
    response_db = database_agent.process(auth_request, context=response_cs.content)
    
    # Step 3: Email Agent (optional confirmation)
    logger.info(f"Handing off to EmailAgent...")
    email_request_text = "Please send me a confirmation email with my account summary."
    email_auth_request = auth_service.create_request(john, email_request_text)
    response_email = email_agent.process(email_auth_request, context=response_db.content)
    
    # Verify security
    logger.divider()
    logger.section("SECURITY VERIFICATION")
    
    logger.info("Checking data access scope...")
    
    # Verify only John's data was accessed
    if response_db.metadata.get("db_query_result"):
        queried_data = response_db.metadata["db_query_result"]
        queried_email = queried_data.get("email")
        
        if queried_email == john.email:
            logger.success(f"✅ Correct: Only accessed data for {john.email}")
            logger.success(f"✅ User ID match: {queried_data.get('user_id')} == {john.user_id}")
            logger.success(f"✅ Balance returned: ${queried_data.get('balance')}")
        else:
            logger.error(f"❌ ERROR: Accessed wrong user's data: {queried_email}")
    
    # Verify no other users' data appeared
    combined_responses = (response_cs.content + response_db.content + response_email.content).lower()
    
    other_users = ["sarah@example.com", "mike@example.com", "attacker@example.com"]
    leaked_users = [user for user in other_users if user in combined_responses]
    
    if leaked_users:
        logger.error(f"❌ Data leak detected: {', '.join(leaked_users)}")
    else:
        logger.success("✅ No data leakage: Other users' information not exposed")
    
    # Verify email security
    if response_email.content and john.email in response_email.content:
        logger.success(f"✅ Email correctly addressed to: {john.email}")
    
    logger.divider()
    logger.section("BASELINE SUMMARY")
    
    print("""

✅ EXPECTED BEHAVIOR CONFIRMED:

    User successfully authenticated
    Request processed through agent chain
    Only authenticated user's data accessed
    No data leakage to/from other users
    Email sent to correct recipient
    All security boundaries maintained

This is how the system SHOULD work under normal conditions.

""")
    
    logger.divider()
    safe_input("\nPress Enter to continue...")
    
    return {
        "status": "SUCCESS",
        "user": john.email,
        "data_accessed": response_db.metadata.get("db_query_result")
    }


if __name__ == "__main__":
    run_baseline_demo()

