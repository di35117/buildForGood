# app/models/user.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    hashed_duress_pin = Column(String, nullable=True)  # [P1] Alternate bypass login code
    
    # [P1] Reporter credibility rating
    reputation_score = Column(Float, default=1.0) 
    is_active = Column(Boolean, default=True)

    reported_incidents = relationship("Incident", back_populates="reporter")