from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from .client import WhoopClient
from ...models.whoop import WhoopUser, WhoopWorkout, WhoopSleep, WhoopRecovery, WhoopCycle

logger = logging.getLogger(__name__)

class WhoopSyncError(Exception):
    """Base exception for Whoop sync errors"""
    pass

class WhoopSync:
    def __init__(
        self,
        db: Session,
        username: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.db = db
        self.username = username
        self.password = password
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_id = None

        # Determine authentication method and initialize user_id
        if self.access_token:
            # If using OAuth tokens, fetch the profile to get the user_id
            try:
                with WhoopClient(access_token=self.access_token, refresh_token=self.refresh_token) as client:
                    profile = client.get_profile()
                    self.user_id = profile.get('user_id')
            except Exception as e:
                logger.error(f"Error fetching profile using OAuth tokens: {e}")
                raise WhoopSyncError(f"Failed to initialize OAuth user: {e}")
        elif self.username and self.password:
            # Legacy: use username/password to look up user record in database
            user = self.db.query(WhoopUser).filter_by(email=self.username).first()
            if user:
                self.user_id = user.user_id
        else:
            raise ValueError("Must provide either OAuth tokens or username/password for authentication.")

    def _get_client(self):
        """Return a WhoopClient instance based on the available authentication method."""
        if self.access_token:
            return WhoopClient(access_token=self.access_token, refresh_token=self.refresh_token)
        else:
            return WhoopClient(username=self.username, password=self.password)

    def get_last_sync_time(self, table) -> Optional[datetime]:
        """Get the most recent updated_at time from a table or None if table is empty"""
        try:
            # Check if the table has any records
            has_records = self.db.query(table).first() is not None
            if not has_records:
                logger.info(f"No existing records found in {table.__tablename__}")
                return None
            # If records exist, get the most recent updated_at value
            from sqlalchemy import select, func
            result = self.db.execute(select(func.max(table.updated_at))).scalar()
            logger.info(f"Last sync time for {table.__tablename__}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            raise WhoopSyncError(f"Database error getting last sync time: {e}")

    def sync_user_data(self) -> WhoopUser:
        """Sync basic user profile and measurements"""
        try:
            client = self._get_client()
            with client as client_instance:
                logger.info("Fetching user profile and measurements")
                profile = client_instance.get_profile()
                measurements = client_instance.get_body_measurement()

            # Check if user record exists and update or create accordingly
            user = self.db.query(WhoopUser).filter_by(user_id=profile['user_id']).first()
            if not user:
                logger.info(f"Creating new user record for user_id: {profile['user_id']}")
                user = WhoopUser(
                    user_id=profile['user_id'],
                    email=profile['email'],
                    first_name=profile['first_name'],
                    last_name=profile['last_name'],
                    height_meter=measurements['height_meter'],
                    weight_kilogram=measurements['weight_kilogram'],
                    max_heart_rate=measurements['max_heart_rate']
                )
                self.db.add(user)
            else:
                logger.info(f"Updating existing user record for user_id: {profile['user_id']}")
                for key, value in profile.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                for key, value in measurements.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

            self.db.commit()
            return user

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during user sync: {e}")
            raise WhoopSyncError(f"Error during user sync: {e}")

    def sync_workouts(self, start_date: Optional[str] = None) -> List[WhoopWorkout]:
        """Sync workout data from last sync time or start_date"""
        try:
            if not start_date:
                last_sync = self.get_last_sync_time(WhoopWorkout)
                start_date = last_sync.isoformat() if last_sync else None

            logger.info(f"Syncing workouts from {start_date or 'all time'}")
            synced_workouts = []
            client = self._get_client()
            with client as client_instance:
                workouts = client_instance.get_workout_collection(start_date=start_date)
                for workout_data in workouts:
                    workout = self._process_workout(workout_data)
                    synced_workouts.append(workout)
            self.db.commit()
            logger.info(f"Successfully synced {len(synced_workouts)} workouts")
            return synced_workouts

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during workout sync: {e}")
            raise WhoopSyncError(f"Error during workout sync: {e}")

    def sync_sleep(self, start_date: Optional[str] = None) -> List[WhoopSleep]:
        """Sync sleep data from last sync time or start_date"""
        try:
            if not start_date:
                last_sync = self.get_last_sync_time(WhoopSleep)
                start_date = last_sync.isoformat() if last_sync else None

            logger.info(f"Syncing sleep data from {start_date or 'all time'}")
            synced_sleeps = []
            client = self._get_client()
            with client as client_instance:
                sleeps = client_instance.get_sleep_collection(start_date=start_date)
                for sleep_data in sleeps:
                    sleep = self._process_sleep(sleep_data)
                    synced_sleeps.append(sleep)
            self.db.commit()
            logger.info(f"Successfully synced {len(synced_sleeps)} sleep records")
            return synced_sleeps

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during sleep sync: {e}")
            raise WhoopSyncError(f"Error during sleep sync: {e}")

    def sync_recovery(self, start_date: Optional[str] = None) -> List[WhoopRecovery]:
        """Sync recovery data from last sync time or start_date"""
        try:
            if not start_date:
                last_sync = self.get_last_sync_time(WhoopRecovery)
                start_date = last_sync.isoformat() if last_sync else None

            logger.info(f"Syncing recovery data from {start_date or 'all time'}")
            synced_recoveries = []
            client = self._get_client()
            with client as client_instance:
                recoveries = client_instance.get_recovery_collection(start_date=start_date)
                for recovery_data in recoveries:
                    recovery = self._process_recovery(recovery_data)
                    synced_recoveries.append(recovery)
            self.db.commit()
            logger.info(f"Successfully synced {len(synced_recoveries)} recovery records")
            return synced_recoveries

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during recovery sync: {e}")
            raise WhoopSyncError(f"Error during recovery sync: {e}")

    def sync_cycles(self, start_date: Optional[str] = None) -> List[WhoopCycle]:
        """Sync cycle data from last sync time or start_date"""
        try:
            if not start_date:
                last_sync = self.get_last_sync_time(WhoopCycle)
                start_date = last_sync.isoformat() if last_sync else None

            logger.info(f"Syncing cycles from {start_date or 'all time'}")
            synced_cycles = []
            client = self._get_client()
            with client as client_instance:
                cycles = client_instance.get_cycle_collection(start_date=start_date)
                for cycle_data in cycles:
                    cycle = self._process_cycle(cycle_data)
                    synced_cycles.append(cycle)
            self.db.commit()
            logger.info(f"Successfully synced {len(synced_cycles)} cycles")
            return synced_cycles

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during cycle sync: {e}")
            raise WhoopSyncError(f"Error during cycle sync: {e}")

    def _process_workout(self, workout_data: Dict[str, Any]) -> WhoopWorkout:
        """Process a single workout record"""
        workout = self.db.query(WhoopWorkout).filter_by(id=workout_data['id']).first()
        if not workout:
            # Convert sport_id to int if necessary
            sport_id = int(workout_data['sport_id'])
            workout = WhoopWorkout(
                id=workout_data['id'],
                user_id=workout_data['user_id'],
                sport_id=sport_id,
                created_at=datetime.fromisoformat(workout_data['created_at'].rstrip('Z')),
                updated_at=datetime.fromisoformat(workout_data['updated_at'].rstrip('Z')),
                start=datetime.fromisoformat(workout_data['start'].rstrip('Z')),
                end=datetime.fromisoformat(workout_data['end'].rstrip('Z')),
                timezone_offset=workout_data['timezone_offset'],
                score_state=workout_data['score_state'],
                raw_score=workout_data.get('score')
            )
            if 'score' in workout_data and workout_data['score']:
                score = workout_data['score']
                workout.strain = score.get('strain')
                workout.average_heart_rate = score.get('average_heart_rate')
                workout.max_heart_rate = score.get('max_heart_rate')
                workout.kilojoule = score.get('kilojoule')
                workout.percent_recorded = score.get('percent_recorded')
                workout.distance_meter = score.get('distance_meter')
                workout.altitude_gain_meter = score.get('altitude_gain_meter')
                workout.altitude_change_meter = score.get('altitude_change_meter')
                
                zone_duration = score.get('zone_duration', {})
                workout.zone_zero_milli = zone_duration.get('zone_zero_milli')
                workout.zone_one_milli = zone_duration.get('zone_one_milli')
                workout.zone_two_milli = zone_duration.get('zone_two_milli')
                workout.zone_three_milli = zone_duration.get('zone_three_milli')
                workout.zone_four_milli = zone_duration.get('zone_four_milli')
                workout.zone_five_milli = zone_duration.get('zone_five_milli')
            self.db.add(workout)
        return workout

    def _process_sleep(self, sleep_data: Dict[str, Any]) -> WhoopSleep:
        """Process a single sleep record"""
        sleep = self.db.query(WhoopSleep).filter_by(id=sleep_data['id']).first()
        if not sleep:
            sleep = WhoopSleep(
                id=sleep_data['id'],
                user_id=sleep_data['user_id'],
                created_at=datetime.fromisoformat(sleep_data['created_at'].rstrip('Z')),
                updated_at=datetime.fromisoformat(sleep_data['updated_at'].rstrip('Z')),
                start=datetime.fromisoformat(sleep_data['start'].rstrip('Z')),
                end=datetime.fromisoformat(sleep_data['end'].rstrip('Z')),
                timezone_offset=sleep_data['timezone_offset'],
                nap=sleep_data['nap'],
                score_state=sleep_data['score_state'],
                raw_score=sleep_data.get('score')
            )
            if 'score' in sleep_data and sleep_data['score']:
                score = sleep_data['score']
                stage_summary = score.get('stage_summary', {})
                sleep.total_in_bed_time_milli = stage_summary.get('total_in_bed_time_milli')
                sleep.total_awake_time_milli = stage_summary.get('total_awake_time_milli')
                sleep.total_no_data_time_milli = stage_summary.get('total_no_data_time_milli')
                sleep.total_light_sleep_time_milli = stage_summary.get('total_light_sleep_time_milli')
                sleep.total_slow_wave_sleep_time_milli = stage_summary.get('total_slow_wave_sleep_time_milli')
                sleep.total_rem_sleep_time_milli = stage_summary.get('total_rem_sleep_time_milli')
                sleep.sleep_cycle_count = stage_summary.get('sleep_cycle_count')
                sleep.disturbance_count = stage_summary.get('disturbance_count')
                sleep_needed = score.get('sleep_needed', {})
                sleep.baseline_milli = sleep_needed.get('baseline_milli')
                sleep.need_from_sleep_debt_milli = sleep_needed.get('need_from_sleep_debt_milli')
                sleep.need_from_recent_strain_milli = sleep_needed.get('need_from_recent_strain_milli')
                sleep.need_from_recent_nap_milli = sleep_needed.get('need_from_recent_nap_milli')
                sleep.respiratory_rate = score.get('respiratory_rate')
                sleep.sleep_performance_percentage = score.get('sleep_performance_percentage')
                sleep.sleep_consistency_percentage = score.get('sleep_consistency_percentage')
                sleep.sleep_efficiency_percentage = score.get('sleep_efficiency_percentage')
            self.db.add(sleep)
        return sleep

    def _process_recovery(self, recovery_data: Dict[str, Any]) -> WhoopRecovery:
        """Process a single recovery record"""
        recovery = self.db.query(WhoopRecovery).filter_by(cycle_id=recovery_data['cycle_id']).first()
        if not recovery:
            recovery = WhoopRecovery(
                cycle_id=recovery_data['cycle_id'],
                sleep_id=recovery_data['sleep_id'],
                user_id=recovery_data['user_id'],
                created_at=datetime.fromisoformat(recovery_data['created_at'].rstrip('Z')),
                updated_at=datetime.fromisoformat(recovery_data['updated_at'].rstrip('Z')),
                score_state=recovery_data['score_state'],
                raw_score=recovery_data.get('score')
            )
            if 'score' in recovery_data and recovery_data['score']:
                score = recovery_data['score']
                recovery.user_calibrating = score.get('user_calibrating')
                recovery.recovery_score = score.get('recovery_score')
                recovery.resting_heart_rate = score.get('resting_heart_rate')
                recovery.hrv_rmssd_milli = score.get('hrv_rmssd_milli')
                recovery.spo2_percentage = score.get('spo2_percentage')
                recovery.skin_temp_celsius = score.get('skin_temp_celsius')
            self.db.add(recovery)
        return recovery

    def _process_cycle(self, cycle_data: Dict[str, Any]) -> WhoopCycle:
        """Process a single cycle record"""
        cycle = self.db.query(WhoopCycle).filter_by(id=cycle_data['id']).first()
        if not cycle:
            cycle = WhoopCycle(
                id=cycle_data['id'],
                user_id=cycle_data['user_id'],
                created_at=datetime.fromisoformat(cycle_data['created_at'].rstrip('Z')),
                updated_at=datetime.fromisoformat(cycle_data['updated_at'].rstrip('Z')),
                start=datetime.fromisoformat(cycle_data['start'].rstrip('Z')),
                end=datetime.fromisoformat(cycle_data['end'].rstrip('Z')) if cycle_data.get('end') else None,
                timezone_offset=cycle_data['timezone_offset'],
                score_state=cycle_data['score_state'],
                raw_score=cycle_data.get('score')
            )
            if 'score' in cycle_data and cycle_data['score']:
                score = cycle_data['score']
                cycle.strain = score.get('strain')
                cycle.kilojoule = score.get('kilojoule')
                cycle.average_heart_rate = score.get('average_heart_rate')
                cycle.max_heart_rate = score.get('max_heart_rate')
            self.db.add(cycle)
        return cycle
