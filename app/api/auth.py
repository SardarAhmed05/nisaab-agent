from fastapi import APIRouter, Depends, HTTPException
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


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


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
    session: AsyncSession = Depends(get_session)
):

    result = await session.execute(
        select(User).where(
            User.email == request.email
        )
    )

    user = result.scalar_one_or_none()


    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    if not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


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