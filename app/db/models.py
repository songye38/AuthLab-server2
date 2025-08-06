
# sqlalchemy 모델 정의
# 이 파일은 데이터베이스 테이블 구조를 정의합니다.




from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base,engine
import app.db.models as models


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


# User 모델 정의
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)  # ✅ 여기 꼭 있어야 DB에 저장됨
    posts = relationship("Post", back_populates="owner")


class Post(models.Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="posts")