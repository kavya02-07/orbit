"""
Authentication routes — register, login, and me.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserRegister, UserOut, TokenResponse
from app.core.security import create_access_token, get_current_user_id
from app.utils.password import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == payload.email)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    stmt = select(User).where(User.id == current_user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)
