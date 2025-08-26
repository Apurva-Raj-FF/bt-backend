"""
Authentication Routes Module

This module defines all authentication-related API endpoints including:
- User registration and login
- Google OAuth integration
- Password reset functionality
- Email verification
- User profile management
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.database.database import SessionLocal
from app.database.models import User, UserRole
from app.auth.service import (
    hash_password,
    create_access_token,
    verify_password,
    get_google_token,
    get_google_user,
    send_google_welcome_email,  # Add this import
    send_reset_email,
    send_verification_email,
    update_user_details_service
)
from app.auth.schemas import UserCreate, UserLogin, UserResponse, UpdateUserRequest
import os
from datetime import timedelta
from fastapi import Form
import jwt

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

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user (UserCreate): User registration data
        db (Session): Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If email is already registered
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        password_hash=hashed_password,
        role=UserRole.STANDARD_USER,  # Default role assigned
        is_verified=False  # Email needs verification
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send welcome email
    send_verification_email(new_user.email)

    return new_user

@router.get("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Verify user's email address.
    
    Args:
        token (str): Verification token
        db (Session): Database session
        
    Returns:
        RedirectResponse: Redirects to frontend after verification
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    db.commit()
    
    # Redirect to frontend after successful verification
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Default to localhost if env variable is missing
    return RedirectResponse(url=f"{frontend_url}/email-verified", status_code=303)  # 303 ensures a proper GET request

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Authenticate user and return access token.
    
    Args:
        user (UserLogin): User login credentials
        db (Session): Database session
        
    Returns:
        dict: Access token and user role
        
    Raises:
        HTTPException: If credentials are invalid
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token({"sub": db_user.email, "role": db_user.role.value})  # Convert Enum to string
    print("token", token, "role", db_user.role.value)
    return {"token": token, "role": db_user.role.value}

@router.get("/google/login")
def google_login() -> RedirectResponse:
    """
    Redirect to Google OAuth login page.
    
    Returns:
        RedirectResponse: Redirects to Google OAuth page
    """
    google_auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&response_type=code&scope=openid%20email%20profile"
    return RedirectResponse(url=google_auth_url)

@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    
    Args:
        request (Request): FastAPI request object
        db (Session): Database session
        
    Returns:
        RedirectResponse: Redirects to frontend with token
        
    Raises:
        HTTPException: If authorization code is missing or invalid
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    token_data = get_google_token(code)
    user_info = get_google_user(token_data)
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not fetch user info")
    
    existing_user = db.query(User).filter(User.email == user_info["email"]).first()
    if not existing_user:
        new_user = User(
            name=user_info["name"],
            email=user_info["email"],
            google_id=user_info["id"],
            is_verified=True,
            role=UserRole.STANDARD_USER  # Default role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        existing_user = new_user
        
        # Send welcome email to new users
        send_google_welcome_email(existing_user.email)
    
    token = create_access_token({"sub": existing_user.email, "role": existing_user.role.value})
    print("token", token, "role", existing_user.role.value)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{FRONTEND_URL}/google/callback?email={existing_user.email}&token={token}&role={existing_user.role.value}")   

@router.post("/forgot-password")
def forgot_password(email: str = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    """
    Send password reset email.
    
    Args:
        email (str): User's email address
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If email is not found
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    reset_token = create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=15))
    send_reset_email(user.email, reset_token)
    
    return {"message": "Password reset link sent to your email."}

@router.post("/reset-password")
def reset_password(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)) -> dict:
    """
    Reset user's password.
    
    Args:
        token (str): Password reset token
        new_password (str): New password
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"message": "Password successfully reset."}

@router.post("/get-user-detail")
def get_user_details(email: str = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    """
    Get user details by email.
    
    Args:
        email (str): User's email address
        db (Session): Database session
        
    Returns:
        dict: User details or not found message
    """
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        return {"message": "User not found"}

    # Convert to dictionary if it's an ORM object
    user_details = {
        "name": db_user.name,
        "email": db_user.email,
        "phone_number": db_user.mobile,
        "isVerfied": db_user.is_verified
    }

    return {"user_details": user_details}

@router.put("/update-user-details")
def update_user_details(request: UpdateUserRequest, db: Session = Depends(get_db)) -> dict:
    """
    Update user details.
    
    Args:
        request (UpdateUserRequest): Updated user details
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user is not found
    """
    return update_user_details_service(request, db)