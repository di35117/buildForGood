import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ForumPost(Base):
    """
    Module 3 [P1]: Anonymous peer Q&A. 
    Skin A: Menstrual Health | Skin B: DV Support
    """
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    
    # 🔥 FIX: Structural Anonymity. Real ID is never stored.
    author_hash = Column(String, nullable=False, index=True)
    
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, index=True, default="menstrual_health") 
    
    is_anonymous = Column(Boolean, default=True)
    requires_human_review = Column(Boolean, default=False, index=True) 
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    replies = relationship("ForumReply", back_populates="post", cascade="all, delete-orphan")


class ForumReply(Base):
    """Replies to the anonymous forum posts."""
    __tablename__ = "forum_replies"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False)
    
    # 🔥 FIX: Structural Anonymity.
    author_hash = Column(String, nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    
    is_anonymous = Column(Boolean, default=True)
    requires_human_review = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("ForumPost", back_populates="replies")