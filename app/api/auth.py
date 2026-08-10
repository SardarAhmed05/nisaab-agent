from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    TokenResponse,
    GoogleAuthRequest
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

    ip_key = f"ip:{client_ip}"

    if (
        is_login_blocked(ip_key)
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
        
        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password"
        )


    if not verify_password(
        request.password,
        user.password_hash
    ):
        record_failed_login(ip_key)

        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password"
        )
    
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


@router.get("/google/config")
async def google_config():
    import os
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    return {"client_id": client_id}


@router.post(
    "/google",
    response_model=TokenResponse
)
async def google_auth(
    request: GoogleAuthRequest,
    session: AsyncSession = Depends(get_session)
):
    import json
    import urllib.request
    from app.db.crud import get_or_create_user

    credential = request.credential.strip()
    if not credential:
        raise HTTPException(status_code=400, detail="Google credential required")

    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        req = urllib.request.Request(url, headers={"User-Agent": "Nisaab-Server/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as err:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {err}")

    google_sub = data.get("sub")
    email = data.get("email")
    name = data.get("name") or data.get("given_name") or "Google User"

    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Invalid Google payload")

    user = await get_or_create_user(
        session,
        platform="google",
        platform_id=google_sub,
        username=email.split("@")[0],
        name=name
    )

    if not user.email:
        user.email = email
        await session.commit()

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