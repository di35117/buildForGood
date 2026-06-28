from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.support import ForumPost, ForumReply
from app.models.user import User
from app.services.gemini_service import moderate_forum_post

router = APIRouter()

class ReplyCreate(BaseModel):
    content: str

class ReplyResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    # Notice we do NOT expose author_id to maintain complete anonymity

class PostCreate(BaseModel):
    title: str
    content: str
    category: str = "menstrual_health"

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    created_at: datetime
    replies: List[ReplyResponse] = []

@router.post("/posts", response_model=PostResponse)
async def create_anonymous_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Creates a new anonymous post and runs it through the AI Moderator."""
    # 1. AI Safety Check (Runs in background thread so server doesn't freeze)
    is_crisis = await run_in_threadpool(moderate_forum_post, post_in.content)
    
    # 2. Get User
    user = db.query(User).filter(User.username == current_user).first()
    
    # 3. Save to DB
    new_post = ForumPost(
        author_id=user.id if user else None,
        title=post_in.title,
        content=post_in.content,
        category=post_in.category,
        requires_human_review=is_crisis # 🔥 Hidden from public feed if True!
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post

@router.get("/posts", response_model=List[PostResponse])
def get_safe_posts(
    category: str = "menstrual_health",
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Fetches all approved, non-crisis posts for the community feed."""
    posts = db.query(ForumPost).filter(
        ForumPost.category == category,
        ForumPost.requires_human_review == False # 🔥 Only show safe posts!
    ).order_by(ForumPost.created_at.desc()).all()
    
    return posts

@router.post("/posts/{post_id}/replies", response_model=ReplyResponse)
async def create_reply(
    post_id: int,
    reply_in: ReplyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P1] Adds an anonymous reply to a specific post."""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # AI Safety check for replies too
    is_crisis = await run_in_threadpool(moderate_forum_post, reply_in.content)
    
    user = db.query(User).filter(User.username == current_user).first()
    
    new_reply = ForumReply(
        post_id=post_id,
        author_id=user.id if user else None,
        content=reply_in.content,
        requires_human_review=is_crisis
    )
    
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    
    return new_reply