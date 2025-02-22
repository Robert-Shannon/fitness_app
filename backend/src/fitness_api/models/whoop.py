from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class WhoopScoreState(enum.Enum):
    SCORED = "SCORED"
    PENDING_SCORE = "PENDING_SCORE"
    UNSCORABLE = "UNSCORABLE"

class WhoopSport(enum.IntEnum):
    ACTIVITY = -1
    RUNNING = 0
    CYCLING = 1
    BASEBALL = 16
    BASKETBALL = 17
    ROWING = 18
    FENCING = 19
    FIELD_HOCKEY = 20
    FOOTBALL = 21
    GOLF = 22
    ICE_HOCKEY = 24
    LACROSSE = 25
    RUGBY = 27
    SAILING = 28
    SKIING = 29
    SOCCER = 30
    SOFTBALL = 31
    SQUASH = 32
    SWIMMING = 33
    TENNIS = 34
    TRACK_AND_FIELD = 35
    VOLLEYBALL = 36
    WATER_POLO = 37
    WRESTLING = 38
    BOXING = 39
    DANCE = 42
    PILATES = 43
    YOGA = 44
    WEIGHTLIFTING = 45
    CROSS_COUNTRY_SKIING = 47
    FUNCTIONAL_FITNESS = 48
    DUATHLON = 49
    GYMNASTICS = 51
    HIKING_RUCKING = 52
    HORSEBACK_RIDING = 53
    KAYAKING = 55
    MARTIAL_ARTS = 56
    MOUNTAIN_BIKING = 57
    POWERLIFTING = 59
    ROCK_CLIMBING = 60
    PADDLEBOARDING = 61
    TRIATHLON = 62
    WALKING = 63
    SURFING = 64
    ELLIPTICAL = 65
    STAIRMASTER = 66
    MEDITATION = 70
    OTHER = 71
    DIVING = 73
    OPERATIONS_TACTICAL = 74
    OPERATIONS_MEDICAL = 75
    OPERATIONS_FLYING = 76
    OPERATIONS_WATER = 77
    ULTIMATE = 82
    CLIMBER = 83
    JUMPING_ROPE = 84
    AUSTRALIAN_FOOTBALL = 85
    SKATEBOARDING = 86
    COACHING = 87
    ICE_BATH = 88
    COMMUTING = 89
    GAMING = 90
    SNOWBOARDING = 91
    MOTOCROSS = 92
    CADDYING = 93
    OBSTACLE_COURSE_RACING = 94
    MOTOR_RACING = 95
    HIIT = 96
    SPIN = 97
    JIU_JITSU = 98
    MANUAL_LABOR = 99
    CRICKET = 100
    PICKLEBALL = 101
    INLINE_SKATING = 102
    BOX_FITNESS = 103
    SPIKEBALL = 104
    WHEELCHAIR_PUSHING = 105
    PADDLE_TENNIS = 106
    BARRE = 107
    STAGE_PERFORMANCE = 108
    HIGH_STRESS_WORK = 109
    PARKOUR = 110
    GAELIC_FOOTBALL = 111
    HURLING_CAMOGIE = 112
    CIRCUS_ARTS = 113
    MASSAGE_THERAPY = 121
    STRENGTH_TRAINER = 123
    WATCHING_SPORTS = 125
    ASSAULT_BIKE = 126
    KICKBOXING = 127
    STRETCHING = 128
    TABLE_TENNIS = 230
    BADMINTON = 231
    NETBALL = 232
    SAUNA = 233
    DISC_GOLF = 234
    YARD_WORK = 235
    AIR_COMPRESSION = 236
    PERCUSSIVE_MASSAGE = 237
    PAINTBALL = 238
    ICE_SKATING = 239
    HANDBALL = 240
    F45_TRAINING = 248
    PADEL = 249
    BARRYS = 250
    DEDICATED_PARENTING = 251
    STROLLER_WALKING = 252
    STROLLER_JOGGING = 253
    TODDLERWEARING = 254
    BABYWEARING = 255
    BARRE3 = 258
    HOT_YOGA = 259
    STADIUM_STEPS = 261
    POLO = 262
    MUSICAL_PERFORMANCE = 263
    KITE_BOARDING = 264
    DOG_WALKING = 266
    WATER_SKIING = 267
    WAKEBOARDING = 268
    COOKING = 269
    CLEANING = 270
    PUBLIC_SPEAKING = 272


class WhoopUser(Base):
    __tablename__ = "whoop_users"
    
    # Primary identifier and basic profile fields
    user_id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    
    # Body measurements
    height_meter = Column(Float, nullable=False)
    weight_kilogram = Column(Float, nullable=False)
    max_heart_rate = Column(Integer, nullable=False)

    # Relationships
    workouts = relationship("WhoopWorkout", back_populates="user")
    sleep = relationship("WhoopSleep", back_populates="user")
    recoveries = relationship("WhoopRecovery", back_populates="user")
    cycles = relationship("WhoopCycle", back_populates="user")

    # Relationships
    workouts = relationship("WhoopWorkout", back_populates="user")
    sleep = relationship("WhoopSleep", back_populates="user")
    recoveries = relationship("WhoopRecovery", back_populates="user")
    cycles = relationship("WhoopCycle", back_populates="user")

class WhoopWorkout(Base):
    __tablename__ = "whoop_workouts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('whoop_users.user_id'), nullable=False)
    sport_id = Column(Enum(WhoopSport), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    timezone_offset = Column(String, nullable=False)
    score_state = Column(Enum(WhoopScoreState), nullable=False)
    
    # Raw score data
    raw_score = Column(JSONB)
    
    # Breaking out score fields
    strain = Column(Float)
    average_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    kilojoule = Column(Float)
    percent_recorded = Column(Float)
    distance_meter = Column(Float)
    altitude_gain_meter = Column(Float)
    altitude_change_meter = Column(Float)

    # Zone duration fields (in milliseconds)
    zone_zero_milli = Column(Integer)
    zone_one_milli = Column(Integer)
    zone_two_milli = Column(Integer)
    zone_three_milli = Column(Integer)
    zone_four_milli = Column(Integer)
    zone_five_milli = Column(Integer)

    # Relationships
    user = relationship("WhoopUser", back_populates="workouts")

class WhoopSleep(Base):
    __tablename__ = "whoop_sleep"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('whoop_users.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    timezone_offset = Column(String, nullable=False)
    nap = Column(Boolean, nullable=False)
    score_state = Column(Enum(WhoopScoreState), nullable=False)
    
    # Raw score data
    raw_score = Column(JSONB)
    
    # Stage Summary fields (in milliseconds)
    total_in_bed_time_milli = Column(Integer)
    total_awake_time_milli = Column(Integer)
    total_no_data_time_milli = Column(Integer)
    total_light_sleep_time_milli = Column(Integer)
    total_slow_wave_sleep_time_milli = Column(Integer)
    total_rem_sleep_time_milli = Column(Integer)
    sleep_cycle_count = Column(Integer)
    disturbance_count = Column(Integer)
    
    # Sleep Needed fields (in milliseconds)
    baseline_milli = Column(Integer)
    need_from_sleep_debt_milli = Column(Integer)
    need_from_recent_strain_milli = Column(Integer)
    need_from_recent_nap_milli = Column(Integer)
    
    # Score fields
    respiratory_rate = Column(Float)
    sleep_performance_percentage = Column(Float)
    sleep_consistency_percentage = Column(Float)
    sleep_efficiency_percentage = Column(Float)

    # Relationships
    user = relationship("WhoopUser", back_populates="sleep")
    recovery = relationship("WhoopRecovery", back_populates="sleep")

class WhoopRecovery(Base):
    __tablename__ = "whoop_recovery"
    
    cycle_id = Column(Integer, ForeignKey('whoop_cycles.id'), primary_key=True)
    sleep_id = Column(Integer, ForeignKey('whoop_sleep.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('whoop_users.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    score_state = Column(Enum(WhoopScoreState), nullable=False)
    
    # Raw score data
    raw_score = Column(JSONB)
    
    # Breaking out score fields
    user_calibrating = Column(Boolean)
    recovery_score = Column(Integer)
    resting_heart_rate = Column(Integer)
    hrv_rmssd_milli = Column(Float)
    spo2_percentage = Column(Float)
    skin_temp_celsius = Column(Float)

    # Relationships
    user = relationship("WhoopUser", back_populates="recoveries")
    sleep = relationship("WhoopSleep", back_populates="recovery")
    cycle = relationship("WhoopCycle", back_populates="recovery")

class WhoopCycle(Base):
    __tablename__ = "whoop_cycles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('whoop_users.user_id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime)  # Can be null if cycle is ongoing
    timezone_offset = Column(String, nullable=False)
    score_state = Column(Enum(WhoopScoreState), nullable=False)
    
    # Raw score data
    raw_score = Column(JSONB)
    
    # Breaking out score fields
    strain = Column(Float)
    kilojoule = Column(Float)
    average_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)

    # Relationships
    user = relationship("WhoopUser", back_populates="cycles")
    recovery = relationship("WhoopRecovery", back_populates="cycle", uselist=False)