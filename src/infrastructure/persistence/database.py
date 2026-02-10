from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Why: Need a centralized place for DB connections
# Base model for all ORM models
Base = declarative_base()

class Database:
    def __init__(self, db_url: str):
        # Check if SQLite is used (needs check_same_thread=False)
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        
        self.engine = create_engine(
            db_url, 
            connect_args=connect_args
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )

    def get_db(self):
        """Dependency for getting DB session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
