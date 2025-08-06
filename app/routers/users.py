from fastapi import APIRouter, Depends, HTTPException, Response,Request
from sqlalchemy.orm import Session
import app.db.models as models
from app.db.schemas import UserCreate, UserOut, UserLogin, TokenOut
from app.db.crud import create_user, get_user_by_email, verify_password
from app.auth.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,create_refresh_token,REFRESH_TOKEN_EXPIRE_DAYS
from app.auth.dependencies import verify_token, get_current_user
from app.db.database import get_db
#import jwt
from datetime import timedelta
from dotenv import load_dotenv
import os
from jose import JWTError, jwt



load_dotenv()  # 이거 꼭 해줘야 함
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")  # .env 파일에서 리프레시 토큰 키 가져오기
ALGORITHM = "HS256"


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일이에요.")
    new_user = create_user(db, email=user.email, password=user.password)
    return new_user


@router.post("/login", response_model=TokenOut)
async def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 틀렸습니다.")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 예: 7일
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="리프레시 토큰 없음")

    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="리프레시 토큰 유효하지 않음")
    except JWTError:
        raise HTTPException(status_code=401, detail="리프레시 토큰 만료 또는 유효하지 않음")

    # 새 access_token 발급
    new_access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response.set_cookie("access_token", new_access_token, httponly=True, secure=True, samesite="none")
    return {"message": "access token 재발급 완료"}






@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="none",  # 있어도 되고 없어도 됨 (delete에는 영향 적음)
        secure=True
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="none",  # 있어도 되고 없어도 됨 (delete에는 영향 적음)
        secure=True
    )
    return {"msg": "로그아웃 완료"}

@router.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="인증된 사용자가 없습니다")
    return {"email": current_user.email, "id": current_user.id}


@router.get("/protected")
async def protected_route(user_id: str = Depends(verify_token)):
    return {"message": f"안녕하세요, {user_id}님! 인증된 사용자입니다."}
