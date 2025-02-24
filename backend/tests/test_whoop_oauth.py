import os
import logging
import webbrowser
import secrets  # <-- Import secrets to generate state
from urllib.parse import urlencode
import requests
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fitness_api.services.auth.service import AuthService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Create a test database session"""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set in .env")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def test_whoop_auth():
    """Test the Whoop OAuth flow with fixed redirect URL"""
    db = None
    try:
        load_dotenv()
        client_id = os.getenv("WHOOP_CLIENT_ID")
        client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        # Use a redirect URI that is registered for your Whoop app.
        redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "https://www.whoop.com/us/en/examples/")

        if not all([client_id, client_secret]):
            raise ValueError(
                "Missing required environment variables. Please ensure WHOOP_CLIENT_ID "
                "and WHOOP_CLIENT_SECRET are set in your .env file"
            )

        # Setup database session
        db = setup_database()
        
        # Initialize auth service
        auth_service = AuthService(db)

        # Step 1: Generate a state parameter and authorization URL
        state = secrets.token_hex(4)  # Generates an 8-character hex string
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "offline read:profile read:workout read:sleep read:recovery",
            "redirect_uri": redirect_uri,
            "state": state
        }
        auth_url = f"https://api.prod.whoop.com/oauth/oauth2/auth?{urlencode(auth_params)}"
        
        logger.info("\nStep 1: Opening authorization URL in your browser...")
        logger.info("You will be redirected to the examples page after login.")
        logger.info("The URL will contain the authorization code and state.")
        webbrowser.open(auth_url)

        logger.info("\nAfter logging in, you'll see an error page (this is expected).")
        logger.info("Look in your browser's address bar for 'code=' and copy the code value only.")
        
        # Step 2: Get the code from user
        auth_code = input("\nEnter ONLY the authorization code: ").strip()
        if not auth_code:
            raise ValueError("No authorization code provided.")

        # Optionally, you could also ask the user to verify the state parameter if needed.

        # Step 3: Exchange code for tokens
        logger.info("\nExchanging code for tokens...")
        token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        token_response = requests.post(token_url, data=token_data, headers=headers)
        logger.info(f"Token response status: {token_response.status_code}")
        if token_response.status_code != 200:
            raise Exception(f"Token exchange failed: {token_response.text}")
            
        tokens = token_response.json()
        logger.info("Successfully received tokens!")
        logger.info(f"Access Token: {tokens['access_token'][:10]}...")
        logger.info(f"Refresh Token: {tokens['refresh_token'][:10]}...")
        logger.info(f"Expires in: {tokens['expires_in']} seconds")

        # Step 4: Test the token with a profile request
        logger.info("\nTesting token with a profile request...")
        profile_response = requests.get(
            "https://api.prod.whoop.com/developer/v1/user/profile/basic",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        logger.info(f"Profile response status: {profile_response.status_code}")
        if profile_response.status_code == 200:
            profile = profile_response.json()
            logger.info(f"Success! Connected to Whoop user: {profile['first_name']} {profile['last_name']}")
            
            # Create or update user in your database
            test_user = auth_service.get_or_create_user(
                email=profile['email'],
                first_name=profile['first_name'],
                last_name=profile['last_name']
            )
            
            # Store tokens in database
            auth_service.update_whoop_tokens(
                user_id=test_user.id,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_in=tokens['expires_in'],
                whoop_user_id=str(profile['user_id']),
                scope=tokens.get('scope', '')
            )
            logger.info("Successfully stored tokens in database")
        else:
            logger.error(f"Profile request failed: {profile_response.text}")

    except Exception as e:
        logger.error(f"Error during OAuth flow: {e}")
        raise
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    test_whoop_auth()
