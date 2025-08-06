
# 이 파일은 사용자 인증과 관련된 CRUD 작업을 수행하는 모듈입니다.
# 사용자 생성, 조회, 비밀번호 해시화 및 검증 기능을 포함합니다.
# 이 모듈은 FastAPI와 SQLAlchemy를 사용하여 데이터베이스와 상호작용합니다.


from sqlalchemy.orm import Session
from app.db.models import User
from passlib.context import CryptContext
from app.db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 비밀번호 해시 함수
def get_password_hash(password: str):
    return pwd_context.hash(password)

# 사용자 생성 함수
def create_user(db: Session, email: str, password: str,name: str):
    hashed_pw = get_password_hash(password) #비밀번호를 해시 함수에 넣어서 해시 값을 구함
    db_user = User(email=email, hashed_password=hashed_pw,name=name) 
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 사용자 조회 함수 추가
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# 비밀번호 검증 함수
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)