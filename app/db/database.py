
# 이 파일은 SQLAlchemy를 사용하여 데이터베이스와 상호작용합니다

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv
import os

load_dotenv()  # 이거 꼭 해줘야 함

DATABASE_URL = os.getenv("DATABASE_URL")  # 이건 .env에 설정하거나 Railway에 입력

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


#DB 세션을 만들어 주는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
