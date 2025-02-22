import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fitness_api.services.whoop.sync import WhoopSync
from fitness_api.models.whoop import Base

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

if __name__ == "__main__":
    test_whoop_sync()