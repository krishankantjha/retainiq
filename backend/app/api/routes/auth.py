from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import Token
from app.services.auth_service import authenticate_user
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, retrieve a JWT access token for future requests.
    This endpoint supports interactive login in Swagger UI.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(subject=user)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


from app.schemas.auth import UserCreate, UserResponse, PasswordReset
from app.database.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.config import settings

from sqlalchemy.exc import SQLAlchemyError

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account with secure Bcrypt password hashing and security questions."""
    # Check if username is settings.ADMIN_USERNAME
    if user_in.username.lower() == settings.ADMIN_USERNAME.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    try:
        # Check if user already exists in db
        existing_user = db.query(User).filter(User.username == user_in.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
            
        # Hash password and security answer (case insensitive & stripped)
        hashed = get_password_hash(user_in.password)
        sec_ans_clean = user_in.security_answer.strip().lower()
        hashed_sec_ans = get_password_hash(sec_ans_clean)
        
        new_user = User(
            username=user_in.username, 
            hashed_password=hashed,
            security_question=user_in.security_question,
            security_answer_hash=hashed_sec_ans
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database tables not found. Please run database migrations first."
        )


@router.get("/security-question/{username}")
def get_security_question(username: str, db: Session = Depends(get_db)):
    """Fetch the security question registered by the user."""
    # Handle settings ADMIN user
    if username.lower() == settings.ADMIN_USERNAME.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin credentials are managed via config. Security question recovery is not available."
        )
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Username not found"
        )
    
    if not user.security_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No security question registered for this user."
        )
        
    return {"security_question": user.security_question}


@router.post("/reset-password")
def reset_password(reset_in: PasswordReset, db: Session = Depends(get_db)):
    """Verify the security question answer and update the password."""
    username = reset_in.username
    if username.lower() == settings.ADMIN_USERNAME.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin credentials are managed via config and cannot be reset."
        )
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Username not found"
        )
        
    if not user.security_answer_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user does not have a registered security answer."
        )
        
    # Verify security answer (case insensitive & stripped)
    ans_clean = reset_in.security_answer.strip().lower()
    if not verify_password(ans_clean, user.security_answer_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect answer to the security question."
        )
        
    # Update password
    user.hashed_password = get_password_hash(reset_in.new_password)
    try:
        db.add(user)
        db.commit()
        return {"success": True, "message": "Password reset successful. Please sign in with your new password."}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password in database."
        )
