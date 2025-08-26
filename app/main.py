"""
FastAPI Application Entry Point

This module serves as the main entry point for the FastAPI application.
It initializes the FastAPI app, sets up CORS middleware, and includes all routers.
"""

from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.strategy.routes import router as strategy_router
from app.database.database import engine
from app.database.database import Base
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI application
app = FastAPI(
    title="FFPU API",
    description="FastAPI backend for FFPU application",
    version="1.0.0"
)

# Configure CORS middleware
# Allows all origins, methods, and headers for development
# In production, you should restrict these to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers with their respective prefixes and tags
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(strategy_router, prefix="/api/strategy", tags=["Strategy"])