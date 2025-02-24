# src/fitness_api/api/v1/endpoints/auth/whoop.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from src.fitness_api.core.database import get_db
from src.fitness_api.core.config import Settings
from src.fitness_api.services.auth.service import AuthService
from src.fitness_api.services.whoop.oauth import WhoopOAuthHandler, WhoopOAuthError

settings = Settings()
router = APIRouter()

oauth_handler = WhoopOAuthHandler(
    client_id=settings.WHOOP_CLIENT_ID,
    client_secret=settings.WHOOP_CLIENT_SECRET
)

@router.get("/whoop/authorize")
async def authorize_whoop(db: Session = Depends(get_db)):
    """
    Start Whoop OAuth flow.
    Returns the authorization URL for the frontend to redirect to.
    """
    try:
        # Get the authorization URL and state
        auth_url, state = oauth_handler.get_authorization_url()
        
        # Return both URL and state to the frontend
        return {
            "authorization_url": auth_url,
            "state": state
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )

@router.get("/whoop/callback")
async def whoop_callback(
    code: str,
    state: str,
    user_id: int,  # The authenticated user's ID
    db: Session = Depends(get_db)
):
    """
    Handle Whoop OAuth callback.
    Exchanges auth code for tokens and stores them in the database.
    """
    try:
        # Exchange code for tokens
        token_data = oauth_handler.exchange_code_for_token(code)
        
        # Get user profile from Whoop using the new access token
        profile = oauth_handler.get_user_profile(token_data["access_token"])
        
        # Initialize auth service
        auth_service = AuthService(db)
        
        # Store tokens in database
        auth_service.update_whoop_tokens(
            user_id=user_id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
            whoop_user_id=str(profile["user_id"]),
            scope=token_data.get("scope", "")
        )
        
        return {
            "message": "Successfully connected to Whoop",
            "user": {
                "whoop_id": profile["user_id"],
                "first_name": profile["first_name"],
                "last_name": profile["last_name"]
            }
        }
        
    except WhoopOAuthError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process OAuth callback: {str(e)}"
        )

@router.get("/whoop/refresh")
async def refresh_whoop_token(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Refresh Whoop access token using stored refresh token
    """
    try:
        auth_service = AuthService(db)
        
        # Get current tokens
        tokens = auth_service.get_whoop_tokens(user_id)
        if not tokens:
            raise HTTPException(
                status_code=404,
                detail="No Whoop connection found"
            )
        
        # Refresh the token
        new_tokens = oauth_handler.refresh_token(tokens.refresh_token)
        
        # Update stored tokens
        auth_service.update_whoop_tokens(
            user_id=user_id,
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens.get("refresh_token", tokens.refresh_token),
            expires_in=new_tokens["expires_in"],
            whoop_user_id=tokens.whoop_user_id,
            scope=new_tokens.get("scope", tokens.scope)
        )
        
        return {"message": "Successfully refreshed Whoop tokens"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh token: {str(e)}"
        )

@router.delete("/whoop/disconnect")
async def disconnect_whoop(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Disconnect Whoop integration by removing stored tokens
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.remove_whoop_connection(user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="No Whoop connection found"
            )
            
        return {"message": "Successfully disconnected from Whoop"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect: {str(e)}"
        )