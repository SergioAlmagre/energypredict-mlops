from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth_protection import login_failure_guard
from app.core.config import get_settings
from app.core.rate_limit import limit_by_ip
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserMe, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=payload.role.value, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(
        limit_by_ip(
            scope="auth_login",
            limit=get_settings().login_rate_limit_requests,
            window_seconds=get_settings().login_rate_limit_window_seconds,
        )
    ),
):
    settings = get_settings()
    client_host = request.client.host if request.client else "unknown"
    lock_key = f"{form_data.username}:{client_host}"
    login_failure_guard.ensure_allowed(
        key=lock_key,
        max_attempts=settings.login_failed_attempts_limit,
        window_seconds=settings.login_failed_attempts_window_seconds,
    )

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        login_failure_guard.register_failure(
            key=lock_key,
            window_seconds=settings.login_failed_attempts_window_seconds,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    login_failure_guard.register_success(lock_key)
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)


@router.get("/me", response_model=UserMe)
def me(current_user: User = Depends(get_current_user)):
    return current_user
