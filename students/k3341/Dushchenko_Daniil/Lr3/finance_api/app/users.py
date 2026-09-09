from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import User, UserCreate, UserRead, UserReadWithRelations, UserUpdate, PasswordChange, Token
from app.security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(tags=["Пользователи"])


@router.post("/auth/register", response_model=UserRead, status_code=201)
@router.post("/users", response_model=UserRead, status_code=201)
def register(data: UserCreate, session: Session = Depends(get_session)) -> User:
    user = User(email=str(data.email).lower(), full_name=data.full_name,
                hashed_password=hash_password(data.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Email уже зарегистрирован")
    session.refresh(user)
    return user


@router.post("/auth/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> Token:
    user = session.exec(select(User).where(User.email == form.username.lower())).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_token(user))


@router.get("/users/me", response_model=UserReadWithRelations)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/users/me/password", status_code=204)
def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Response:
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(400, "Неверный текущий пароль")
    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1  # Старые токены перестают действовать.
    session.add(user)
    session.commit()
    return Response(status_code=204)


@router.get("/users", response_model=list[UserRead])
def users(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[User]:
    return list(session.exec(select(User)).all())


@router.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, user: User = Depends(get_current_user),
              session: Session = Depends(get_session)) -> User:
    found = session.get(User, user_id)
    if found is None:
        raise HTTPException(404, "Пользователь не найден")
    return found


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: UserUpdate, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)) -> User:
    if user_id != user.id:
        raise HTTPException(403, "Можно менять только свой профиль")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, str(value).lower() if key == "email" else value)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Email уже зарегистрирован")
    session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)) -> Response:
    if user_id != user.id:
        raise HTTPException(403, "Можно удалить только свой профиль")
    if user.operations or user.categories:
        raise HTTPException(409, "Сначала удалите операции и категории")
    session.delete(user)
    session.commit()
    return Response(status_code=204)
