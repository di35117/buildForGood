from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)

    user = relationship("User", back_populates="emergency_contacts")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True) 
    hashed_password = Column(String, nullable=False)
    hashed_duress_pin = Column(String, nullable=True) 
    reputation_score = Column(Float, default=1.0) 
    is_active = Column(Boolean, default=True)
    
    is_ngo = Column(Boolean, default=False, index=True)

    reported_incidents = relationship("Incident", back_populates="reporter")
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")