import os
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    UserResponse,
    AuthTokenResponse,
)
from app.services.auth_service import AuthService, JWT_SECRET, JWT_ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def signup(req: UserSignupRequest, db: Session = Depends(get_db)):
    """Register a new user account into the database and return JWT token."""
    svc = AuthService(db)
    return svc.signup(req)


@router.post("/login", response_model=AuthTokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials against the database and return JWT token."""
    svc = AuthService(db)
    return svc.login(req)


@router.post("/google", response_model=AuthTokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register a user via Google OAuth."""
    svc = AuthService(db)
    return svc.google_auth(req)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Fetch current user profile using Bearer JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token.",
        )

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return UserResponse.model_validate(user)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired.",
        )
