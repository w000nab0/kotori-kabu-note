from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.services.user_service import UserService
from app.core.database import get_db
from app.core.auth import get_current_user, get_current_active_user
from app.core.security import verify_token

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """新規ユーザー登録"""
    db_user = UserService.create_user(db, user)
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        nickname=db_user.nickname,
        email_verified=db_user.email_verified,
        created_at=db_user.created_at,
        last_login=db_user.last_login
    )

@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """ユーザーログイン"""
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    tokens = UserService.create_tokens(user)
    return Token(**tokens)

@router.post("/login-json", response_model=Token)
async def login_user_json(user: UserLogin, db: Session = Depends(get_db)):
    """JSONでユーザーログイン"""
    db_user = UserService.authenticate_user(db, user.email, user.password)
    tokens = UserService.create_tokens(db_user)
    return Token(**tokens)

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """トークンリフレッシュ"""
    try:
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # ユーザー存在確認
        import uuid
        user = UserService.get_user_by_id(db, uuid.UUID(user_id))
        
        # 新しいトークン生成
        tokens = UserService.create_tokens(user)
        return Token(**tokens)
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """現在のユーザー情報取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )