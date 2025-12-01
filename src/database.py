"""
PostgreSQL Database Module
Handles database operations for SecureBank customer data
"""

import config
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from src.utils import logger


class DatabaseService:
    """PostgreSQL database service for SecureBank"""
    
    def __init__(self):
        self.query_log = []
        self.connection = None
        self.use_postgres = config.DB_USE_POSTGRES
        
        if self.use_postgres:
            self._connect()
    
    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        """Convert non-JSON-serializable types to JSON-safe types"""
        if isinstance(value, Decimal):
            return str(value)
        elif hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat()
        return value
    
    def _connect(self):
        """Establish PostgreSQL connection"""
        try:
            self.connection = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD
            )
            logger.info(f"Connected to PostgreSQL database: {config.DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            logger.warning("Falling back to mock database")
            self.use_postgres = False
            self.connection = None
    
    def _get_connection(self):
        """Get database connection, reconnect if needed"""
        if not self.use_postgres:
            return None
        
        try:
            if self.connection is None or self.connection.closed:
                self._connect()
            return self.connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries
        
        Returns:
            List of dictionaries representing rows
        """
        if not self.use_postgres:
            # Fallback to mock data
            return self._fallback_query(query)
        
        conn = self._get_connection()
        if not conn:
            return self._fallback_query(query)
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                # Log the query
                self.query_log.append({
                    "type": "EXECUTE",
                    "query": query,
                    "params": params,
                    "timestamp": str(datetime.now())
                })
                
                # Fetch results
                if cursor.description:
                    results = cursor.fetchall()
                    # Convert Decimal and other non-JSON-serializable types to strings/floats
                    json_safe_results = []
                    for row in results:
                        row_dict = {k: self._make_json_safe(v) for k, v in dict(row).items()}
                        json_safe_results.append(row_dict)
                    return json_safe_results
                else:
                    conn.commit()
                    return []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            conn.rollback()
            raise
    
    def _fallback_query(self, query: str) -> List[Dict[str, Any]]:
        """Fallback to mock data if PostgreSQL not available"""
        query_upper = query.upper().strip()
        
        if "SELECT * FROM customers" in query_upper or "SELECT * FROM CUSTOMERS" in query_upper:
            if "WHERE 1=1" in query_upper or "WHERE" not in query_upper:
                return list(config.CUSTOMER_DATABASE.values())
        
        # Try to extract user_id from WHERE clause
        if "WHERE" in query_upper:
            # Simple extraction - in production, use proper SQL parsing
            if "user_id" in query_upper.lower():
                # Extract user_id value (simplified)
                parts = query_upper.split("USER_ID")
                if len(parts) > 1:
                    value_part = parts[1].split()[0] if len(parts[1].split()) > 0 else None
                    if value_part and value_part.isdigit():
                        user_data = config.CUSTOMER_DATABASE.get(value_part)
                        return [user_data] if user_data else []
        
        return []
    
    def query_user_data(self, user_id: str, fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Query data for a specific user
        
        Args:
            user_id: The user ID to query
            fields: Optional list of specific fields to return
        
        Returns:
            User data dict or None if not found
        """
        if self.use_postgres:
            field_list = ", ".join(fields) if fields else "*"
            query = f"SELECT {field_list} FROM customers WHERE user_id = %s"
            results = self.execute_query(query, (user_id,))
            return results[0] if results else None
        else:
            # Fallback to mock
            query = {
                "type": "SELECT",
                "user_id": user_id,
                "fields": fields or ["all"],
                "timestamp": str(datetime.now())
            }
            self.query_log.append(query)
            
            user_data = config.CUSTOMER_DATABASE.get(user_id)
            if not user_data:
                return None
            
            if fields:
                return {k: v for k, v in user_data.items() if k in fields or k == "user_id"}
            
            return user_data.copy()
    
    def query_all_users(self) -> List[Dict[str, Any]]:
        """
        Query ALL users - THIS SHOULD NEVER BE CALLED IN PRODUCTION
        This exists only to demonstrate the attack
        """
        if self.use_postgres:
            query = "SELECT * FROM customers"
            return self.execute_query(query)
        else:
            # Fallback to mock
            query = {
                "type": "SELECT_ALL",
                "warning": "DANGEROUS_QUERY",
                "timestamp": str(datetime.now())
            }
            self.query_log.append(query)
            return list(config.CUSTOMER_DATABASE.values())
    
    def get_balance(self, user_id: str) -> Optional[float]:
        """Get user's account balance"""
        user_data = self.query_user_data(user_id, fields=["balance"])
        return user_data.get("balance") if user_data else None
    
    def get_account_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's account summary (safe fields only)"""
        safe_fields = ["user_id", "email", "name", "account_type", "balance"]
        return self.query_user_data(user_id, fields=safe_fields)
    
    def detect_suspicious_query(self, query_text: str) -> bool:
        """Detect potentially malicious query patterns"""
        suspicious_patterns = [
            "DROP TABLE",
            "DELETE FROM",
            "TRUNCATE",
            "ALTER TABLE",
            "CREATE TABLE",
            "INSERT INTO",
            "UPDATE",
            "--",
            "';",
            "UNION SELECT"
        ]
        
        query_upper = query_text.upper()
        for pattern in suspicious_patterns:
            if pattern in query_upper:
                return True
        return False
    
    def get_query_log(self) -> List[Dict]:
        """Return query log for analysis"""
        return self.query_log.copy()
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()


# Global database service instance
db_service = DatabaseService()
