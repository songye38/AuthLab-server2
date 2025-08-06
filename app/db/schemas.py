# pydantic 모델 정의
# 이 파일은 사용자 생성 및 출력 모델을 정의합니다.
# Pydantic은 데이터 유효성 검사 및 설정 관리를 위한 라이브러리
# FastAPI와 함께 사용되어 API 요청 및 응답의 데이터 구조를 정의합니다.


from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str  # ✅ 닉네임 추가!

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class PostCreate(BaseModel):
    title: str
    content: str
