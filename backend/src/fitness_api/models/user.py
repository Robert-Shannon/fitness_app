from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # For email/password login
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships with OAuth connections
    whoop_connection = relationship("WhoopOAuthConnection", back_populates="user", uselist=False)
    strava_connection = relationship("StravaOAuthConnection", back_populates="user", uselist=False)
    garmin_connection = relationship("GarminOAuthConnection", back_populates="user", uselist=False)

class OAuthBaseConnection(Base):
    """Abstract base class for OAuth connections"""
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    access_token = Column(String)
    refresh_token = Column(String)
    token_type = Column(String)
    expires_at = Column(DateTime(timezone=True))
    scope = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WhoopOAuthConnection(OAuthBaseConnection):
    __tablename__ = "whoop_oauth_connections"

    user = relationship("User", back_populates="whoop_connection")
    whoop_user_id = Column(String)  # Whoop's internal user ID

class StravaOAuthConnection(OAuthBaseConnection):
    __tablename__ = "strava_oauth_connections"

    user = relationship("User", back_populates="strava_connection")
    athlete_id = Column(String)  # Strava's athlete ID

class GarminOAuthConnection(OAuthBaseConnection):
    __tablename__ = "garmin_oauth_connections"

    user = relationship("User", back_populates="garmin_connection")
    garmin_user_id = Column(String)  # Garmin's user ID