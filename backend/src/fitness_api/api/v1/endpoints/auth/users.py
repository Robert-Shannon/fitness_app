from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.fitness_api.core.database import get_db
from src.fitness_api.models.user import User
from src.fitness_api.schemas.auth import UserCreate, UserResponse, UserUpdate

router = APIRouter()

# Configure the password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    The provided password is hashed before being stored.
    """
    # Check if a user with the provided email already exists.
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Hash the plain-text password.
    hashed_password = pwd_context.hash(user.password)
    
    # Create a new User instance.
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=True,    # New users are active by default.
        is_verified=False  # Adjust verification logic as needed.
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update the user's email, first name, and/or last name.
    This is a crude endpoint for testing updates.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    # Update fields if they are provided.
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name

    # Commit the changes and refresh the user instance.
    db.commit()
    db.refresh(user)
    
    return user
