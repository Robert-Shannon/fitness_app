# src/fitness_api/services/whoop/oauth.py

import secrets
from typing import Optional, Tuple
from urllib.parse import urlencode
import requests
from datetime import datetime

from ...core.config import Settings

settings = Settings()

class WhoopOAuthError(Exception):
    """Base exception for Whoop OAuth errors"""
    pass

class WhoopOAuthHandler:
    """Handle Whoop OAuth flow"""
    
    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
    API_URL = "https://api.prod.whoop.com/developer"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self) -> Tuple[str, str]:
        """Generate authorization URL and state parameter"""
        state = secrets.token_hex(16)
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "offline read:profile read:workout read:sleep read:recovery",
            "state": state,
            "redirect_uri": settings.WHOOP_REDIRECT_URI
        }
        
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        return auth_url, state

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for tokens"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise WhoopOAuthError(f"Token exchange failed: {str(e)}")

    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise WhoopOAuthError(f"Token refresh failed: {str(e)}")

    def get_user_profile(self, access_token: str) -> dict:
        """Get user profile information"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.API_URL}/v1/user/profile/basic",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise WhoopOAuthError(f"Failed to get user profile: {str(e)}")