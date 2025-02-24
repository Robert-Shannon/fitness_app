# src/fitness_api/services/auth/service.py

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...models.user import User, WhoopOAuthConnection
from ...core.config import Settings

settings = Settings()

class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    pass

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: str, first_name: str, last_name: str) -> User:
        """Create a new user"""
        try:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=True  # Since we're using Auth0, users are pre-verified
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise AuthenticationError(f"Error creating user: {str(e)}")

    def get_or_create_user(self, email: str, first_name: str, last_name: str) -> User:
        """Get existing user or create new one"""
        user = self.get_user_by_email(email)
        if not user:
            user = self.create_user(email, first_name, last_name)
        return user

    def update_whoop_tokens(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        whoop_user_id: str,
        scope: str
    ) -> WhoopOAuthConnection:
        """Update or create Whoop OAuth tokens for a user"""
        try:
            connection = self.db.query(WhoopOAuthConnection).filter(
                WhoopOAuthConnection.user_id == user_id
            ).first()

            if not connection:
                connection = WhoopOAuthConnection(
                    user_id=user_id,
                    whoop_user_id=whoop_user_id
                )
                self.db.add(connection)

            # Update token information
            connection.access_token = access_token
            connection.refresh_token = refresh_token
            # Convert expires_in seconds to a datetime object
            connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            connection.scope = scope
            connection.token_type = "Bearer"

            self.db.commit()
            self.db.refresh(connection)
            return connection

        except SQLAlchemyError as e:
            self.db.rollback()
            raise AuthenticationError(f"Error updating Whoop tokens: {str(e)}")

    def get_whoop_tokens(self, user_id: int) -> Optional[WhoopOAuthConnection]:
        """Get Whoop OAuth tokens for a user"""
        return self.db.query(WhoopOAuthConnection).filter(
            WhoopOAuthConnection.user_id == user_id
        ).first()

    def remove_whoop_connection(self, user_id: int) -> bool:
        """Remove Whoop OAuth connection for a user"""
        try:
            connection = self.db.query(WhoopOAuthConnection).filter(
                WhoopOAuthConnection.user_id == user_id
            ).first()
            
            if connection:
                self.db.delete(connection)
                self.db.commit()
                return True
            return False

        except SQLAlchemyError as e:
            self.db.rollback()
            raise AuthenticationError(f"Error removing Whoop connection: {str(e)}")