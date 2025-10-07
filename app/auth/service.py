"""
Authentication Service Module

This module handles all authentication-related operations including:
- Password hashing and verification
- JWT token generation and validation
- Google OAuth integration
- Email verification and password reset
- User management operations
"""

import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from app.database.models import User
from app.auth.schemas import UpdateUserRequest
from sqlalchemy.orm import Session
import json

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Initialize password hashing context
# Using bcrypt for secure password hashing
# Update the CryptContext initialization
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # You can adjust the rounds as needed
    bcrypt__ident="2b"  # Explicitly set the bcrypt identifier
)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt algorithm.
    
    Args:
        password (str): The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    max_len = 72
    safe_password = password[:max_len]
    return pwd_context.hash(safe_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The hashed password to verify against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data (dict): The data to encode in the token
        expires_delta (timedelta, optional): Token expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_google_token(code: str) -> str:
    """
    Get Google OAuth access token using authorization code.
    
    Args:
        code (str): The authorization code from Google OAuth
        
    Returns:
        str: The Google access token
        
    Raises:
        HTTPException: If the authorization code is invalid
    """
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI
    }
    response = requests.post(token_url, data=payload)
    token_data = response.json()
    
    if "error" in token_data:
        raise HTTPException(status_code=400, detail="Invalid Google authorization code")
    
    return token_data.get("access_token")

def get_google_user(access_token: str) -> dict:
    """
    Get user information from Google using access token.
    
    Args:
        access_token (str): The Google access token
        
    Returns:
        dict: User information from Google
        
    Raises:
        HTTPException: If unable to retrieve user information
    """
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(user_info_url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve Google user info")
    
    return response.json()
        
def send_reset_email(email: str, token: str) -> None:
    """
    Send password reset email to user.
    
    Args:
        email (str): Recipient's email address
        token (str): Password reset token
    """
    reset_link = f"{os.getenv('FRONTEND_URL')}/reset-password?token={token}"
    subject = "Password Reset Request"
    body = f"Click the link to reset your password: {reset_link}"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["To"] = email
    
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(os.getenv("EMAIL_SENDER"), email, msg.as_string())

def send_email(subject: str, recipient: str, body: str, content_type: str = "plain") -> None:
    """
    Send an email with specified content type.
    
    Args:
        subject (str): Email subject
        recipient (str): Recipient's email address
        body (str): Email body content
        content_type (str, optional): Content type (plain/html). Defaults to "plain".
    """
    msg = MIMEText(body, content_type)
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["To"] = recipient
    
    try:
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            server.sendmail(os.getenv("EMAIL_SENDER"), recipient, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_verification_email(email: str) -> None:
    """
    Send email verification link to user.
    
    Args:
        email (str): Recipient's email address
    """
    verification_token = create_access_token({"sub": email}, expires_delta=timedelta(hours=24))
    verification_link = f"{os.getenv('BACKEND_URL')}/auth/verify-email/{verification_token}"
    dashboard_link = f"{os.getenv('FRONTEND_URL')}/screens"
    docs_link = f"{os.getenv('FRONTEND_URL')}/guides/backtesting"
    
    subject = "Verify Your Email Address"
    
    # Read the email template from file
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email_verification.html')
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Replace the links in the template
    body = template.replace("{verification_link}", verification_link)\
                   .replace("{dashboard_link}", dashboard_link)\
                   .replace("{docs_link}", docs_link)

    send_email(subject, email, body, content_type="html")
def update_user_details_service(request: UpdateUserRequest, db: Session) -> dict:
    """
    Update user details in the database.
    
    Args:
        request (UpdateUserRequest): The update request containing new user details
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user is not found
    """
    from app.auth.service import hash_password
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.name:
        user.name = request.name
    if request.mobile:
        user.mobile = request.mobile
    if request.new_password:
        user.password_hash = hash_password(request.new_password)

    db.commit()
    db.refresh(user)
    
    return {"message": "User details updated successfully"}


import jwt
import os
from datetime import datetime

def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Token payload containing user information
        
    Raises:
        Exception: If token is invalid or expired
    """
    print(token)
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
        print(payload)
        if payload.get("exp") and datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
            raise Exception("Token has expired")
        return payload
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def send_google_welcome_email(email: str) -> None:
    """
    Send welcome email to users who signed up with Google.
    
    Args:
        email (str): Recipient's email address
    """
    dashboard_link = f"{os.getenv('FRONTEND_URL')}/screens"
    docs_link = f"{os.getenv('FRONTEND_URL')}/guides/backtesting"
    
    subject = "Welcome to Fidelfolio!"
    
    # Read the email template from file
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'google_welcome.html')
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Replace the links in the template
    body = template.replace("{dashboard_link}", dashboard_link).replace("{docs_link}", docs_link)

    send_email(subject, email, body, content_type="html")
