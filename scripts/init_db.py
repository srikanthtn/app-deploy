"""
Database initialization script for Stellantis Auth RDS.

This script creates the users table in your Postgres RDS instance.
Run this once to set up the schema.

Usage:
    python -m scripts.init_db
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.infrastructure.persistence.database import Base, Database
from src.infrastructure.persistence.models import UserModel

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database schema"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("Error: DATABASE_URL not found in environment variables")
        print("Make sure .env file exists with DATABASE_URL set")
        return False

    print("Connecting to database...")
    host_display = database_url.split('@')[1] if '@' in database_url else 'hidden'
    print(f"URL(host/db): {host_display}")

    try:
        # Create database instance
        db = Database(database_url)

        # Create all tables defined in models
        print("Creating database tables...")
        Base.metadata.create_all(bind=db.engine)

        print("Database initialization complete!")
        print("Created tables: users")

        return True

    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("\nMost common reasons for RDS timeout:")
        print("1) RDS is NOT public OR you are not on the same VPC/network")
        print("2) Security Group inbound rule doesn't allow your IP on port 5432")
        print("3) Your local network/firewall blocks outbound 5432")
        print("\nBasic fix:")
        print("- In AWS RDS: set 'Public access' = Yes (for quick dev) OR run backend inside the VPC")
        print("- In the RDS Security Group: allow inbound PostgreSQL 5432 from YOUR public IP /32")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Stellantis Auth Database Initialization")
    print("=" * 60)

    success = init_database()

    if success:
        print("\n✅ You can now start the backend server!")
        print("   python run.py")
    else:
        print("\n❌ Failed to initialize database")
        print("   Check your DATABASE_URL and RDS connection")

    print("=" * 60)
