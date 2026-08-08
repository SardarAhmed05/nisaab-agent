from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    TokenResponse
)

from app.db.session import get_session
from app.db.models import User
from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token

import time
from collections import defaultdict

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

LOGIN_MAX_ATTEMPTS = 5
LOGIN_BLOCK_SECONDS = 300  # 5 minutes

login_attempts = defaultdict(list)


def is_login_blocked(key: str) -> bool:
    now = time.time()

    attempts = login_attempts[key]

    # Keep only attempts from the current block window
    attempts[:] = [
        timestamp
        for timestamp in attempts
        if now - timestamp < LOGIN_BLOCK_SECONDS
    ]

    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def record_failed_login(key: str) -> None:
    login_attempts[key].append(time.time())


def clear_login_attempts(key: str) -> None:
    login_attempts.pop(key, None)


@router.post(
    "/signup",
    response_model=SignupResponse
)
async def signup(
    request: SignupRequest,
    session: AsyncSession = Depends(get_session)
):

    existing = await session.execute(
        select(User).where(
            (User.email == request.email) |
            (User.username == request.username)
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )


    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password)
    )


    session.add(user)

    await session.commit()
    await session.refresh(user)


    return {
        "message": "User created",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }



@router.post(
    "/login",
    response_model=TokenResponse
)
async def login(
    request: LoginRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_session)
):

    client_ip = (
        http_request.client.host
        if http_request.client
        else "unknown"
    )

    identifier = request.identifier.strip().lower()

    ip_key = f"ip:{client_ip}"
    identifier_key = f"identifier:{identifier}"

    if (
        is_login_blocked(ip_key)
        or is_login_blocked(identifier_key)
    ):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Please try again later."
        )

    result = await session.execute(
        select(User).where(
            (User.email == request.identifier) |
            (User.username == request.identifier)
        )
    )

    user = result.scalar_one_or_none()


    if user is None:
        record_failed_login(ip_key)
        record_failed_login(identifier_key)

        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password"
        )


    if not verify_password(
        request.password,
        user.password_hash
    ):
        record_failed_login(ip_key)
        record_failed_login(identifier_key)

        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password"
        )
    
    clear_login_attempts(identifier_key)
    clear_login_attempts(ip_key)

    token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email
        }
    )


    return {
        "access_token": token,
        "token_type": "bearer"
    }