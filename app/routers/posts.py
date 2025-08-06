from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import app.db.models as models
from app.db.schemas import PostCreate
from app.auth.dependencies import get_current_user
from app.db.database import get_db

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    redirect_slashes=False  # 이 옵션이 핵심!
)


@router.post("", status_code=201)
def create_post(
    post: PostCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        owner_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/mine")
def read_my_posts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    return posts
