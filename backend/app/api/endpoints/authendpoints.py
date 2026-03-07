from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import database, crud, models
from ..DTO import schemas
from ..DTO.schemas import UserCreate, Token
from ..auth import authhelper

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not authhelper.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = authhelper.timedelta(
        minutes=authhelper.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = authhelper.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=schemas.User)
async def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = authhelper.get_password_hash(user.password)
    db_user = crud.create_user(db, user=user, hashed_password=hashed_password)
    return db_user


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(authhelper.get_current_user),
):
    return current_user
