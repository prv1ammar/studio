from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import User
from app.core.auth import get_password_hash, verify_password, create_access_token, decode_token
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Create user
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        company_name=user_in.company_name,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.flush() # Get user.id without committing

    # Create default workspace for the user
    from app.db.models import Workspace, WorkspaceMember
    workspace = Workspace(
        name="Personal Workspace",
        description=f"Personal space for {new_user.full_name or new_user.email}",
        owner_id=new_user.id
    )
    db.add(workspace)
    await db.flush() # Get workspace.id

    # Add user as owner member of the workspace
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=new_user.id,
        role="owner"
    )
    db.add(membership)
    
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(subject=new_user.id)

    # Log Auth Event
    from app.core.audit import audit_logger
    await audit_logger.log(
        action="user_register", 
        user_id=new_user.id, 
        workspace_id=workspace.id,
        details={"email": new_user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(subject=user.id)

    # Log Auth Event
    from app.core.audit import audit_logger
    await audit_logger.log(action="user_login", user_id=user.id, details={"email": user.email})

    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> User:
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
