import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    UserResponse,
    AuthTokenResponse,
)

JWT_SECRET = os.environ.get("JWT_SECRET", "preptalk-jwt-super-secret-key-32-chars-minimum")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: Optional[str]) -> bool:
        if not hashed_password:
            return False
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    def create_access_token(self, user_id: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def signup(self, req: UserSignupRequest) -> AuthTokenResponse:
        email = req.email.strip().lower()
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists. Please log in.",
            )

        hashed = self.hash_password(req.password)
        name = req.name.strip()
        avatar = (name[0] if name else "C").upper()

        user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            hashed_password=hashed,
            avatar=avatar,
            role="Software Engineer",
            auth_provider="email",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        token = self.create_access_token(user.id, user.email)
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def login(self, req: UserLoginRequest) -> AuthTokenResponse:
        email = req.email.strip().lower()
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not self.verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        token = self.create_access_token(user.id, user.email)
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def google_auth(self, req: GoogleAuthRequest) -> AuthTokenResponse:
        email = req.email.strip().lower()
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            name = req.name.strip() if req.name else email.split("@")[0].title()
            avatar = req.avatar or (name[0] if name else "G").upper()
            user = User(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                avatar=avatar,
                role="Software Engineer",
                auth_provider="google",
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        token = self.create_access_token(user.id, user.email)
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
