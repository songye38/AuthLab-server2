
# 이 파일은 JWT 토큰을 생성하고 검증하는 기능을 제공합니다.     
# FastAPI에서 인증 및 권한 부여를 구현할 때 사용됩니다.


from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.redis import redis_client

load_dotenv()  # 이거 꼭 해줘야 함

SECRET_KEY = os.getenv("SECRET_KEY")  # 이건 .env에 설정하거나 Railway에 입력
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15분 유효
REFRESH_TOKEN_EXPIRE_DAYS = 7


# JWT 토큰 생성 함수
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


# JWT 토큰 검증 함수
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    

 # 토큰이 블랙리스트에 있는지 확인
async def is_token_blacklisted(token: str) -> bool:
    value = await redis_client.get(token)
    return value == b"blacklisted"  # Redis에서 가져온 값은 bytes일 수 있음

