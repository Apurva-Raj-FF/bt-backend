"""
Database Configuration Module

This module handles the database connection setup and session management.
It uses SQLAlchemy as the ORM and supports PostgreSQL as the database backend.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine instance
# This will be used to connect to the database
engine = create_engine(DATABASE_URL)

# Create SessionLocal class for database session management
# autocommit=False: Changes are not automatically committed
# autoflush=False: Changes are not automatically flushed to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base class for SQLAlchemy models
# This will be inherited by all database models
Base = declarative_base()
