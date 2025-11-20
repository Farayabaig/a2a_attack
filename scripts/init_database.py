"""
Initialize PostgreSQL database with SecureBank customer data
Run this script to set up the database schema and populate with test data
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database='postgres',
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config.DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {config.DB_NAME}')
            print(f"✅ Database '{config.DB_NAME}' created")
        else:
            print(f"ℹ️  Database '{config.DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not create database (may already exist): {e}")

def create_schema():
    """Create the customers table schema"""
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Drop table if exists (for clean setup)
    cursor.execute("DROP TABLE IF EXISTS customers CASCADE;")
    
    # Create customers table
    create_table_query = """
    CREATE TABLE customers (
        user_id VARCHAR(50) PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        account_type VARCHAR(50) NOT NULL,
        balance DECIMAL(10, 2) NOT NULL,
        ssn VARCHAR(20) NOT NULL,
        credit_card VARCHAR(50) NOT NULL,
        address TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    print("✅ Customers table created")
    
    cursor.close()
    conn.close()

def populate_data():
    """Populate database with SecureBank customer data (non-redacted)"""
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Customer data - NON-REDACTED for POC demonstration
    customers = [
        ("12345", "john@example.com", "John Doe", "Premium", 5000.00, "123-45-6789", "4532-1234-5678-9010", "123 Main St, New York, NY 10001"),
        ("12346", "sarah@example.com", "Sarah Smith", "Basic", 1200.50, "987-65-4321", "5555-1234-5678-9012", "456 Oak Ave, Chicago, IL 60611"),
        ("12347", "mike@example.com", "Mike Johnson", "Premium", 8500.75, "456-78-9012", "4111-1111-1111-1111", "789 Pine Rd, Los Angeles, CA 90001"),
        ("99999", "attacker@example.com", "Attacker Account", "Basic", 100.00, "000-00-0000", "0000-0000-0000-0000", "Unknown")
    ]
    
    insert_query = """
    INSERT INTO customers (user_id, email, name, account_type, balance, ssn, credit_card, address)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (user_id) DO UPDATE SET
        email = EXCLUDED.email,
        name = EXCLUDED.name,
        account_type = EXCLUDED.account_type,
        balance = EXCLUDED.balance,
        ssn = EXCLUDED.ssn,
        credit_card = EXCLUDED.credit_card,
        address = EXCLUDED.address;
    """
    
    cursor.executemany(insert_query, customers)
    conn.commit()
    
    print(f"✅ Inserted {len(customers)} customer records")
    
    cursor.close()
    conn.close()

def main():
    """Main initialization function"""
    print("=" * 80)
    print("SecureBank Database Initialization")
    print("=" * 80)
    
    if not config.DB_USE_POSTGRES:
        print("⚠️  PostgreSQL is not enabled in config. Set DB_USE_POSTGRES=true in .env")
        return
    
    try:
        print("\n📦 Step 1: Creating database...")
        create_database()
        
        print("\n📋 Step 2: Creating schema...")
        create_schema()
        
        print("\n📊 Step 3: Populating customer data...")
        populate_data()
        
        print("\n" + "=" * 80)
        print("✅ Database initialization complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

