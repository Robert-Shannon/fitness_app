# tests/test_whoop_data.py
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

from fitness_api.services.whoop.client import WhoopClient

def load_credentials():
    """Load Whoop credentials from environment variables"""
    load_dotenv()
    username = os.getenv("WHOOP_USERNAME")
    password = os.getenv("WHOOP_PASSWORD")
    
    if not username or not password:
        raise ValueError("Missing Whoop credentials in .env file")
    
    return username, password

def fetch_and_save_data(client, start_date=None):
    """Fetch data from Whoop API and save to JSON files"""
    # Get the tests directory path and create test_data directory
    current_dir = Path(__file__).parent
    data_dir = current_dir / 'test_data'
    data_dir.mkdir(exist_ok=True)
    
    # Fetch different types of data
    workouts = client.get_workout_collection(start_date=start_date)
    sleep = client.get_sleep_collection(start_date=start_date)
    recovery = client.get_recovery_collection(start_date=start_date)
    
    # Save raw JSON data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name, data in [
        ("workouts", workouts),
        ("sleep", sleep),
        ("recovery", recovery)
    ]:
        filename = data_dir / f"{name}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Saved {name} data to {filename}")
    
    return workouts, sleep, recovery

def analyze_workouts(workouts):
    """Convert workouts data to pandas DataFrame for analysis"""
    # Flatten the nested JSON structure
    flat_workouts = []
    for workout in workouts:
        flat_workout = {
            'id': workout['id'],
            'start': workout['start'],
            'end': workout['end'],
            'sport_id': workout['sport_id'],
            'strain': workout['score'].get('strain'),
            'avg_heart_rate': workout['score'].get('average_heart_rate'),
            'max_heart_rate': workout['score'].get('max_heart_rate'),
            'calories': workout['score'].get('kilojoule'),
            'distance': workout['score'].get('distance_meter')
        }
        flat_workouts.append(flat_workout)
    
    # Convert to DataFrame
    df = pd.DataFrame(flat_workouts)
    
    # Convert timestamp strings to datetime
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    
    # Calculate workout duration
    df['duration_minutes'] = (df['end'] - df['start']).dt.total_seconds() / 60
    
    return df

def main():
    # Load credentials and create client
    username, password = load_credentials()
    
    # Set start date to 30 days ago
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    
    with WhoopClient(username, password) as client:
        # Fetch and save data
        workouts, sleep, recovery = fetch_and_save_data(
            client, 
            start_date=start_date
        )
        
        # Analyze workouts
        workouts_df = analyze_workouts(workouts)
        
        # Print some basic statistics
        print("\nWorkout Statistics:")
        print(f"Total workouts: {len(workouts_df)}")
        print("\nAverage metrics per workout:")
        print(f"Duration: {workouts_df['duration_minutes'].mean():.1f} minutes")
        print(f"Strain: {workouts_df['strain'].mean():.1f}")
        print(f"Heart Rate: {workouts_df['avg_heart_rate'].mean():.1f} bpm")
        
        # Save processed DataFrame to test_data directory
        csv_path = Path(__file__).parent / 'test_data' / 'processed_workouts.csv'
        workouts_df.to_csv(csv_path, index=False)
        print(f"\nSaved processed workout data to {csv_path}")

if __name__ == "__main__":
    main()