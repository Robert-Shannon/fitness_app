import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fitness_api.services.whoop.sync import WhoopSync
from fitness_api.services.auth.service import AuthService
from fitness_api.models.whoop import Base  # Assuming you need this for DB setup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure package loggers
logging.getLogger('fitness_api').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

def setup_database():
    """Create a test database session"""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def test_whoop_sync():
    """Test the Whoop sync process"""
    try:
        # Get credentials from environment
        load_dotenv()
        username = os.getenv("WHOOP_USERNAME")
        password = os.getenv("WHOOP_PASSWORD")

        if not username or not password:
            raise ValueError("Missing Whoop credentials in .env file")

        # Setup database session
        db = setup_database()
        
        # Initialize sync service
        sync_service = WhoopSync(db, username, password)

        # Sync user data first
        logger.info("Syncing user data...")
        user = sync_service.sync_user_data()
        logger.info(f"Synced user: {user.first_name} {user.last_name}")

        # Sync all data types
        logger.info("Syncing workouts...")
        workouts = sync_service.sync_workouts()
        logger.info(f"Synced {len(workouts)} workouts")

        logger.info("Syncing sleep...")
        sleep_records = sync_service.sync_sleep()
        logger.info(f"Synced {len(sleep_records)} sleep records")

        logger.info("Syncing cycles...")
        cycles = sync_service.sync_cycles()
        logger.info(f"Synced {len(cycles)} cycles")

        logger.info("Syncing recovery...")
        recoveries = sync_service.sync_recovery()
        logger.info(f"Synced {len(recoveries)} recovery records")

    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise
    finally:
        db.close()

def test_whoop_sync_by_user(user_id: int):
    """
    Test the Whoop sync process for a given user id.
    
    It first attempts to retrieve Whoop tokens from the database for the user.
    If tokens exist, it uses them for syncing. Otherwise, it falls back to using 
    the legacy username and password provided via environment variables.
    """
    db = setup_database()
    try:
        # Initialize the AuthService to check for existing Whoop tokens
        auth_service = AuthService(db)
        connection = auth_service.get_whoop_tokens(user_id)
        
        if connection:
            logger.info(f"Found Whoop tokens for user id {user_id}. Using tokens for syncing.")
            # Here, we assume WhoopSync can be instantiated with tokens.
            # Adjust the constructor parameters according to your implementation.
            sync_service = WhoopSync(
                db,
                access_token=connection.access_token,
                refresh_token=connection.refresh_token
            )
        else:
            logger.info(f"No tokens found for user id {user_id}. Falling back to username/password.")
            username = os.getenv("WHOOP_USERNAME")
            password = os.getenv("WHOOP_PASSWORD")
            if not username or not password:
                raise ValueError("Missing Whoop credentials in .env file")
            sync_service = WhoopSync(db, username, password)
        
        # Perform the sync operations
        logger.info("Syncing user data...")
        user = sync_service.sync_user_data()
        logger.info(f"Synced user: {user.first_name} {user.last_name}")

        logger.info("Syncing workouts...")
        workouts = sync_service.sync_workouts()
        logger.info(f"Synced {len(workouts)} workouts")

        logger.info("Syncing sleep...")
        sleep_records = sync_service.sync_sleep()
        logger.info(f"Synced {len(sleep_records)} sleep records")

        logger.info("Syncing cycles...")
        cycles = sync_service.sync_cycles()
        logger.info(f"Synced {len(cycles)} cycles")

        logger.info("Syncing recovery...")
        recoveries = sync_service.sync_recovery()
        logger.info(f"Synced {len(recoveries)} recovery records")

    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # test_whoop_sync()
    test_whoop_sync_by_user(1)