from fastapi import APIRouter, Depends, HTTPException, Response,Request
import requests
from fastapi.responses import RedirectResponse
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

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일이에요.")
    new_user = create_user(db, email=user.email, password=user.password, name=user.name)
    return new_user


@router.post("/login", response_model=TokenOut)
async def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 틀렸습니다.")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user  # UserOut 모델과 매핑되어서 자동 변환됨
    }


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

    # refresh_token은 쿠키에 그대로 두고
    # access_token은 JSON 응답으로 내려줌
    return {"access_token": new_access_token}



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
def read_users_me(
    current_user: models.User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="인증된 사용자가 없습니다")

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }






@router.get("/protected")
async def protected_route(user_id: str = Depends(verify_token)):
    return {"message": f"안녕하세요, {user_id}님! 인증된 사용자입니다."}









# 🔹 카카오 로그인
@router.get("/login/kakao")
async def login_kakao():
    return RedirectResponse(
        f"https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
    )



# 🔹 구글 로그인 시작 (이미 네 코드 있음)
@router.get("/login/google")
async def login_google():
    # 구글 OAuth2 인증 URL 생성
    # 브라우저는 이 URL로 이동 → Google 로그인 화면 표시

    scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}" #로그인에 성공하면 이 URL로 돌아옴
        f"&scope={scope}"
    )


# 🔹 카카오 콜백
@router.get("/oauth/kakao/callback")
async def kakao_callback(code: str, response: Response, db: Session = Depends(get_db)):
    # 1. code로 access_token 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    token_res = requests.post(token_url, data=token_data)
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 토큰 요청 실패")
    token_json = token_res.json()
    kakao_access_token = token_json["access_token"]

    # 2. 유저 정보 가져오기
    userinfo_res = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {kakao_access_token}"},
    )
    if userinfo_res.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 가져오기 실패")

    userinfo = userinfo_res.json()
    kakao_account = userinfo.get("kakao_account", {})
    email = kakao_account.get("email")
    name = kakao_account.get("profile", {}).get("nickname", "카카오유저")

    # 3. DB 확인 (없으면 회원가입, 있으면 로그인)
    db_user = get_user_by_email(db, email)
    if not db_user:
        db_user = create_user(db, email=email, password=None, name=name)

    # 4. JWT 발급
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})

    # 5. 쿠키에 저장
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # 6. 프론트로 리다이렉트
    return RedirectResponse(url="/me?login=success")




# 🔹 구글 콜백 (여기서 code 받아 처리)
from fastapi.responses import RedirectResponse

@router.get("/oauth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    # 1. 받은 code로 access_token 요청
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_res = requests.post(token_url, data=token_data)
    token_res.raise_for_status()
    token_json = token_res.json()
    google_access_token = token_json["access_token"]

    # 2. 구글 유저 정보 가져오기
    userinfo_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"},
    )
    userinfo_res.raise_for_status()
    userinfo = userinfo_res.json()
    email = userinfo.get("email")
    name = userinfo.get("name", "구글유저")

    # 3. DB 확인 (없으면 회원가입)
    db_user = get_user_by_email(db, email)
    if not db_user:
        db_user = create_user(db, email=email, password=None, name=name)


    print("구글 유저 정보:", db_user.id)


    # 4. JWT 토큰 발급
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    print("refresh_token:", refresh_token)

    # 5. RedirectResponse 객체에 쿠키 직접 세팅
    redirect = RedirectResponse(url="https://songyeserver.info/me?login=success")

    # 환경에 따라 쿠키 옵션 다르게 설정
    cookie_params = {
        "key": "refresh_token",
        "value": refresh_token,
        "httponly": True,
        "max_age": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    }

    # 배포 환경에서만 secure + samesite + domain 적용
    cookie_params.update({
        "secure": True,
        "samesite": "none",
        "domain": ".songyeserver.info",
    })

    redirect.set_cookie(**cookie_params)

    return redirect
