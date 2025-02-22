# src/fitness_api/services/whoop/sync.py

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, Dict, Any, List
from sqlalchemy.exc import SQLAlchemyError

from .client import WhoopClient
from ...models.whoop import (
    WhoopUser, 
    WhoopWorkout, 
    WhoopSleep, 
    WhoopRecovery,
    WhoopCycle
)

logger = logging.getLogger(__name__)

class WhoopSyncError(Exception):
    """Base exception for Whoop sync errors"""
    pass

class WhoopSync:
    def __init__(self, db: Session, username: str, password: str):
        self.db = db
        self.username = username
        self.password = password
        self.user_id = None

        # Get user_id from database after syncing user data
        user = self.db.query(WhoopUser).filter_by(email=username).first()
        if user:
            self.user_id = user.user_id

    def get_last_sync_time(self, table) -> Optional[datetime]:
        """Get the most recent updated_at time from a table or None if table is empty"""
        try:
            # First just check if table has any records at all
            has_records = self.db.query(table).first() is not None
            
            if not has_records:
                logger.info(f"No existing records found in {table.__tablename__}")
                return None
                
            # If we have records, get the most recent updated_at
            result = self.db.execute(
                select(func.max(table.updated_at))
            ).scalar()
            
            logger.info(f"Last sync time for {table.__tablename__}: {result}")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting last sync time: {e}")
            raise WhoopSyncError(f"Database error getting last sync time: {e}")

    def sync_user_data(self) -> WhoopUser:
        """Sync basic user profile and measurements"""
        try:
            with WhoopClient(self.username, self.password) as client:
                logger.info("Fetching user profile and measurements")
                profile = client.get_profile()
                measurements = client.get_body_measurement()

                user = self.db.query(WhoopUser).filter_by(
                    user_id=profile['user_id']
                ).first()

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
                
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during user sync: {e}")
            raise WhoopSyncError(f"Database error during user sync: {e}")
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

            with WhoopClient(self.username, self.password) as client:
                workouts = client.get_workout_collection(start_date=start_date)
                
                for workout_data in workouts:
                    workout = self._process_workout(workout_data)
                    synced_workouts.append(workout)

                self.db.commit()
                logger.info(f"Successfully synced {len(synced_workouts)} workouts")
                return synced_workouts

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during workout sync: {e}")
            raise WhoopSyncError(f"Database error during workout sync: {e}")
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

            with WhoopClient(self.username, self.password) as client:
                sleeps = client.get_sleep_collection(start_date=start_date)
                
                for sleep_data in sleeps:
                    sleep = self._process_sleep(sleep_data)
                    synced_sleeps.append(sleep)

                self.db.commit()
                logger.info(f"Successfully synced {len(synced_sleeps)} sleep records")
                return synced_sleeps

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during sleep sync: {e}")
            raise WhoopSyncError(f"Database error during sleep sync: {e}")
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

            with WhoopClient(self.username, self.password) as client:
                recoveries = client.get_recovery_collection(start_date=start_date)
                
                for recovery_data in recoveries:
                    recovery = self._process_recovery(recovery_data)
                    synced_recoveries.append(recovery)

                self.db.commit()
                logger.info(f"Successfully synced {len(synced_recoveries)} recovery records")
                return synced_recoveries

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during recovery sync: {e}")
            raise WhoopSyncError(f"Database error during recovery sync: {e}")
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

            with WhoopClient(self.username, self.password) as client:
                cycles = client.get_cycle_collection(start_date=start_date)
                
                for cycle_data in cycles:
                    cycle = self._process_cycle(cycle_data)
                    synced_cycles.append(cycle)

                self.db.commit()
                logger.info(f"Successfully synced {len(synced_cycles)} cycles")
                return synced_cycles

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during cycle sync: {e}")
            raise WhoopSyncError(f"Database error during cycle sync: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during cycle sync: {e}")
            raise WhoopSyncError(f"Error during cycle sync: {e}")

    def _process_workout(self, workout_data: Dict[str, Any]) -> WhoopWorkout:
        """Process a single workout record"""
        workout = self.db.query(WhoopWorkout).filter_by(
            id=workout_data['id']
        ).first()

        logger.debug(f"Processing workout with sport_id: {workout_data['sport_id']} "
                f"of type {type(workout_data['sport_id'])}")

        if not workout:
            # Convert sport_id to int before creating the workout
            sport_id = int(workout_data['sport_id'])  # Add this line
            
            workout = WhoopWorkout(
                id=workout_data['id'],
                user_id=workout_data['user_id'],
                sport_id=sport_id,  # Use the converted integer
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
        sleep = self.db.query(WhoopSleep).filter_by(
            id=sleep_data['id']
        ).first()

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
                # Stage summary
                stage_summary = score.get('stage_summary', {})
                sleep.total_in_bed_time_milli = stage_summary.get('total_in_bed_time_milli')
                sleep.total_awake_time_milli = stage_summary.get('total_awake_time_milli')
                sleep.total_no_data_time_milli = stage_summary.get('total_no_data_time_milli')
                sleep.total_light_sleep_time_milli = stage_summary.get('total_light_sleep_time_milli')
                sleep.total_slow_wave_sleep_time_milli = stage_summary.get('total_slow_wave_sleep_time_milli')
                sleep.total_rem_sleep_time_milli = stage_summary.get('total_rem_sleep_time_milli')
                sleep.sleep_cycle_count = stage_summary.get('sleep_cycle_count')
                sleep.disturbance_count = stage_summary.get('disturbance_count')

                # Sleep needed
                sleep_needed = score.get('sleep_needed', {})
                sleep.baseline_milli = sleep_needed.get('baseline_milli')
                sleep.need_from_sleep_debt_milli = sleep_needed.get('need_from_sleep_debt_milli')
                sleep.need_from_recent_strain_milli = sleep_needed.get('need_from_recent_strain_milli')
                sleep.need_from_recent_nap_milli = sleep_needed.get('need_from_recent_nap_milli')

                # Other metrics
                sleep.respiratory_rate = score.get('respiratory_rate')
                sleep.sleep_performance_percentage = score.get('sleep_performance_percentage')
                sleep.sleep_consistency_percentage = score.get('sleep_consistency_percentage')
                sleep.sleep_efficiency_percentage = score.get('sleep_efficiency_percentage')

            self.db.add(sleep)

        return sleep

    def _process_recovery(self, recovery_data: Dict[str, Any]) -> WhoopRecovery:
        """Process a single recovery record"""
        recovery = self.db.query(WhoopRecovery).filter_by(
            cycle_id=recovery_data['cycle_id']
        ).first()

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
        cycle = self.db.query(WhoopCycle).filter_by(
            id=cycle_data['id']
        ).first()

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