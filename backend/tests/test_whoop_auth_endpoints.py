import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app – adjust the import as needed
from src.fitness_api.main import app

# Create a TestClient for our app
client = TestClient(app)

def test_authorize_whoop():
    """
    Test the /whoop/authorize endpoint returns an authorization URL and state.
    """
    response = client.get("/whoop/authorize")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "state" in data

def test_callback_refresh_disconnect(monkeypatch):
    """
    Test the full OAuth flow: callback, refresh, and disconnect endpoints.
    We simulate the OAuth handler's methods so that they return dummy token data
    and user profile info.
    """
    # Dummy token and profile data to simulate Whoop responses
    dummy_token_data = {
        "access_token": "dummy_access_token",
        "refresh_token": "dummy_refresh_token",
        "expires_in": 3600,
        "scope": "offline read:profile read:workout read:sleep read:recovery read:cycles read:body_measurement"
    }
    dummy_profile = {
        "user_id": 12345,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Patch the methods on WhoopOAuthHandler to return our dummy data
    from src.fitness_api.services.whoop.oauth import WhoopOAuthHandler, WhoopOAuthError

    def dummy_exchange_code_for_token(self, code):
        return dummy_token_data

    def dummy_get_user_profile(self, access_token):
        return dummy_profile

    def dummy_refresh_token(self, refresh_token):
        # For simplicity, return a new dummy token (could be the same as dummy_token_data)
        return {
            "access_token": "refreshed_dummy_access_token",
            "refresh_token": "refreshed_dummy_refresh_token",
            "expires_in": 3600,
            "scope": dummy_token_data["scope"]
        }

    monkeypatch.setattr(WhoopOAuthHandler, "exchange_code_for_token", dummy_exchange_code_for_token)
    monkeypatch.setattr(WhoopOAuthHandler, "get_user_profile", dummy_get_user_profile)
    monkeypatch.setattr(WhoopOAuthHandler, "refresh_token", dummy_refresh_token)

    # Assume the state passed in is "dummy_state" (in practice, this should match what is returned by /authorize)
    dummy_state = "dummy_state"
    test_user_id = 1  # Use a test user ID that your test database recognizes

    # Simulate callback endpoint
    callback_response = client.get(
        "/whoop/callback",
        params={
            "code": "dummy_code",
            "state": dummy_state,
            "user_id": test_user_id
        }
    )
    assert callback_response.status_code == 200
    callback_data = callback_response.json()
    assert "Successfully connected to Whoop" in callback_data["message"]
    assert "user" in callback_data
    assert callback_data["user"]["whoop_id"] == dummy_profile["user_id"]

    # Now test the refresh endpoint
    refresh_response = client.get("/whoop/refresh", params={"user_id": test_user_id})
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "Successfully refreshed Whoop tokens" in refresh_data["message"]

    # Finally, test disconnect endpoint
    disconnect_response = client.delete("/whoop/disconnect", params={"user_id": test_user_id})
    assert disconnect_response.status_code == 200
    disconnect_data = disconnect_response.json()
    assert "Successfully disconnected from Whoop" in disconnect_data["message"]
