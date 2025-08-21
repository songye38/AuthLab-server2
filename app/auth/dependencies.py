import os
from fastapi import Depends
from app.auth.auth import verify_access_token
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials,OAuth2PasswordBearer
from app.auth.auth import verify_access_token, is_token_blacklisted,create_access_token
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.database import get_db
import app.db.models as models
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import timedelta



load_dotenv()  # 이거 꼭 해줘야 함

SECRET_KEY = os.getenv("SECRET_KEY")  # 이건 .env에 설정하거나 Railway에 입력
ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 현재 사용자 정보를 가져오는 함수
# 이 함수는 인증 헤더에서 토큰을 추출하고, 토큰을 검증하여 사용자 ID를 반환합니다.
# 만약 토큰이 블랙리스트에 있다면 예외를 발생시킵니다.
from fastapi import Request

def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 실패",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None

    # 1. 헤더 확인
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. 없으면 쿠키 확인
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user







security = HTTPBearer()

# 🚫 로그아웃된 토큰인지 검사하고, 정상이면 user_id 반환
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    if await is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="로그아웃된 토큰입니다.")

    user_id = verify_access_token(token)
    return user_id