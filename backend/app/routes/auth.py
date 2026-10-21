from fastapi import APIRouter, HTTPException, status, Depends
from ..models.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from ..auth_utils import hash_password, verify_password, create_access_token, get_current_user
from ..db import db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegister):
    existing = await db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_doc = {
        "email": req.email,
        "name": req.name,
        "hashed_password": hash_password(req.password)
    }
    user_id = await db.create_user(user_doc)
    user_doc["id"] = user_id

    access_token = create_access_token({"sub": user_id, "email": req.email})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=req.email, name=req.name)
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin):
    user = await db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user.get("_id", user.get("id")))
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user["email"], name=user.get("name", "User"))
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    return UserResponse(
        id=user_id,
        email=current_user.get("email", ""),
        name=current_user.get("name", "User"),
        created_at=current_user.get("created_at")
    )
