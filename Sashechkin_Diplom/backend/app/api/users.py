from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix='/users', tags=['Users'])


@router.get('', response_model=list[UserResponse])
def list_users(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[UserResponse]:
    _ = admin_user
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    return [UserResponse.model_validate(user) for user in users]


@router.post('', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    _ = admin_user
    duplicate = db.scalar(select(User).where(or_(User.username == payload.username, User.email == payload.email)))
    if duplicate:
        raise HTTPException(status_code=400, detail='Логин или email уже заняты')

    user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch('/{user_id}', response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    _ = admin_user
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = get_password_hash(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get('/specialists', response_model=list[UserResponse])
def list_specialists(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[UserResponse]:
    _ = admin_user
    specialists = db.scalars(select(User).where(User.role == UserRole.specialist).order_by(User.full_name.asc())).all()
    return [UserResponse.model_validate(user) for user in specialists]
