import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set the base URL for your API (adjust if needed)
BASE_URL = "http://localhost:8000/api/v1"

def main():
    # Prompt for the authenticated user's ID (for example, Robert Shannon's user id)
    user_id = input("Enter your user ID (e.g., 1 for Robert Shannon): ").strip()

    # STEP 1: Get the authorization URL and state from the /whoop/authorize endpoint.
    logger.info("Requesting authorization URL...")
    auth_response = requests.get(f"{BASE_URL}/auth/whoop/authorize")
    if auth_response.status_code != 200:
        logger.error(f"Failed to get authorization URL: {auth_response.text}")
        return

    auth_data = auth_response.json()
    logger.info(f"Authorization URL: {auth_data['authorization_url']}")
    logger.info(f"State: {auth_data['state']}")
    logger.info("Please open the above URL in your browser, complete the Whoop login, and then copy the authorization code and state from the redirected URL.")

    # STEP 2: Get the authorization code and state from the user.
    code = input("Enter the authorization code: ").strip()
    state = input("Enter the state returned in the URL: ").strip()

    # STEP 3: Call the /whoop/callback endpoint to exchange the code for tokens.
    logger.info("Exchanging code for tokens via the callback endpoint...")
    callback_params = {
        "code": code,
        "state": state,
        "user_id": user_id
    }
    callback_response = requests.get(f"{BASE_URL}/auth/whoop/callback", params=callback_params)
    if callback_response.status_code != 200:
        logger.error(f"Callback error: {callback_response.text}")
        return

    callback_data = callback_response.json()
    logger.info(f"Callback Response: {callback_data}")

    # STEP 4: Test refreshing the token via the /whoop/refresh endpoint.
    logger.info("Refreshing tokens...")
    refresh_response = requests.get(f"{BASE_URL}/auth/whoop/refresh", params={"user_id": user_id})
    if refresh_response.status_code != 200:
        logger.error(f"Refresh error: {refresh_response.text}")
    else:
        refresh_data = refresh_response.json()
        logger.info(f"Refresh Response: {refresh_data}")

    # STEP 5: Optionally, disconnect Whoop integration via the /whoop/disconnect endpoint.
    disconnect_choice = input("Do you want to disconnect Whoop integration? (y/n): ").strip().lower()
    if disconnect_choice == "y":
        logger.info("Disconnecting Whoop integration...")
        disconnect_response = requests.delete(f"{BASE_URL}/auth/whoop/disconnect", params={"user_id": user_id})
        if disconnect_response.status_code != 200:
            logger.error(f"Disconnect error: {disconnect_response.text}")
        else:
            disconnect_data = disconnect_response.json()
            logger.info(f"Disconnect Response: {disconnect_data}")
    else:
        logger.info("Whoop integration remains connected.")

if __name__ == "__main__":
    main()
