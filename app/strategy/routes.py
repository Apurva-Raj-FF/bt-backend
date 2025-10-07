"""
Strategy Routes Module

This module defines all strategy-related API endpoints including:
- Strategy execution
- Strategy management (save, retrieve, update)
- Portfolio analysis
- Data processing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from app.strategy.schemas import (
    QueryExecutionRequest,
    SaveStrategyRequest,
)
from app.strategy.service import (
    run_script,
    save_strategy_service,
    get_all_strategies_service,
    get_all_strategies_user_service,
    get_strategy_service
)
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.auth.service import verify_jwt_token

# Initialize router
router = APIRouter()

def get_db():
    """
    Dependency function to get database session.
    Ensures proper session cleanup after use.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify JWT token and get current user.
    
    Args:
        credentials: JWT token from Authorization header
        
    Returns:
        dict: User information from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        return verify_jwt_token(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# Add the dependency to all routes that need authentication
@router.post("/execute")
def execute_py(request: QueryExecutionRequest, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Execute a strategy script.
    
    Args:
        request (QueryExecutionRequest): Execution request containing:
            - session_id: Unique identifier for the execution
            - user_token: Authentication token
            - data: Strategy parameters
            
    Returns:
        dict: Execution results or error information
            {
                "status": str,  # "Success" or "Failure"
                "output": str,  # Script output if successful
                "error": str,   # Error message if failed
                "strategy_id": str  # Session ID if successful
            }
            
    Raises:
        HTTPException: If execution fails
    """
    try:
        response = run_script(request.session_id, request.user_token, request.data)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
def save_strategy(request: SaveStrategyRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> dict:
    """
    Save or update a strategy.
    
    Args:
        request (SaveStrategyRequest): Strategy data to save
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If strategy is not found
    """
    return save_strategy_service(request, db)

@router.get("/get_all_strategy_user")
def get_all_strategies(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get all strategies for a specific user with pagination.
    
    Args:
        user_id (str): ID of the user
        page (int): Page number (default: 1)
        page_size (int): Number of items per page (default: 10)
        db (Session): Database session
        
    Returns:
        dict: Paginated list of strategies with their details
    """
    return get_all_strategies_user_service(user_id, page, page_size, db)

@router.get("/get_all_public_strategies")
def get_all_public_strategies(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get all public strategies with pagination.
    
    Args:
        page (int): Page number (default: 1)
        page_size (int): Number of items per page (default: 10)
        db (Session): Database session
        
    Returns:
        dict: Paginated list of strategies
    """
    return get_all_strategies_service(page, page_size, db)

@router.get("/strategies")
def get_strategy(strategy_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get detailed information about a specific strategy with access control.
    
    Args:
        strategy_id (str): ID of the strategy to retrieve
        db (Session): Database session
        current_user (dict, optional): Current authenticated user information
        
    Returns:
        dict: Detailed strategy information
            
    Raises:
        HTTPException: If strategy is not found or access is denied
    """
    # Get the strategy first
    strategy = get_strategy_service(strategy_id, db)
    print("strategy", strategy)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Check if strategy is public
    is_public = strategy.get("ippf", {}).get("isPublic", False)
    strategy_user_id = strategy.get("ippf", {}).get("user_id")
    print("Is Public", is_public)
    
    # If strategy is public, allow access
    if is_public:
        return strategy
    
    # If user is not authenticated, redirect to login
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access this strategy"
        )
    
    # If strategy is private, check if it belongs to the current user
    current_user_id = current_user.get("sub")
    if strategy_user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You don't have permission to view this strategy"
        )
    
    return strategy