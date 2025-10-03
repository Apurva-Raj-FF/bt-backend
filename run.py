#!/usr/bin/env python3
"""
Simple script to run the FFPU FastAPI backend server.
This script sets up basic environment variables and starts the server.
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set default environment variables if not already set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///./ffpu.db"
    print("Using default SQLite database: ./ffpu.db")

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "dev-secret-key-change-in-production"
    print("Using default SECRET_KEY (change in production)")

if not os.getenv("ALGORITHM"):
    os.environ["ALGORITHM"] = "HS256"

if __name__ == "__main__":
    print("Starting FFPU Backend Server...")
    print("API Documentation will be available at: http://localhost:8005/docs")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )

