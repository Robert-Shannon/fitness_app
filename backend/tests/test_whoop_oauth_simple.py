# tests/test_whoop_oauth_simple.py

import os
import logging
from dotenv import load_dotenv
import secrets
import requests
from urllib.parse import urlencode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_oauth_flow():
    """Test basic OAuth flow"""
    try:
        # Load environment variables
        load_dotenv()
        client_id = os.getenv("WHOOP_CLIENT_ID")
        client_secret = os.getenv("WHOOP_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("Missing OAuth credentials in .env file")

        # Generate state parameter (must be 8 characters)
        state = secrets.token_hex(4)  # 8 characters

        # Step 1: Construct authorization URL
        params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "offline read:profile read:workout read:sleep read:recovery",
            "state": state
        }
        
        auth_url = f"https://api.prod.whoop.com/oauth/oauth2/auth?{urlencode(params)}"
        
        logger.info("\nStep 1: Visit this URL in your browser:")
        logger.info(auth_url)
        logger.info("\nAfter authorizing, you'll get an error page (expected), but copy the 'code' from the URL")
        
        # Step 2: Get the code from user
        auth_code = input("\nEnter the authorization code: ").strip()
        returned_state = input("Enter the state parameter from the URL: ").strip()

        # Verify state
        if state != returned_state:
            raise ValueError("State parameter mismatch! Possible CSRF attack")
        
        logger.info("\nStep 3: Exchanging code for tokens...")
        
        # Exchange code for tokens using form data
        token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "offline read:profile read:workout read:sleep read:recovery"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        logger.info("\nMaking token request...")
        token_response = requests.post(
            token_url, 
            data=token_data,  # Using data= instead of json=
            headers=headers
        )
        
        if token_response.status_code == 200:
            tokens = token_response.json()
            logger.info("\nSuccess! Received tokens:")
            logger.info(f"Access Token: {tokens['access_token'][:10]}...")
            logger.info(f"Refresh Token: {tokens['refresh_token'][:10]}...")
            logger.info(f"Expires in: {tokens['expires_in']} seconds")
            
            # Test the token
            logger.info("\nTesting token with a profile request...")
            profile_response = requests.get(
                "https://api.prod.whoop.com/developer/v1/user/profile/basic",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                logger.info(f"Success! Retrieved profile for {profile.get('first_name')} {profile.get('last_name')}")
            else:
                logger.error(f"Profile request failed: {profile_response.text}")
        else:
            logger.error(f"Token exchange failed: {token_response.text}")

    except Exception as e:
        logger.error(f"Error during OAuth flow: {e}")
        raise

if __name__ == "__main__":
    test_oauth_flow()