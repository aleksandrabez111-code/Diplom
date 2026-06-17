from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.ticket import Ticket
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter(prefix='/topics', tags=['Topics'])


def _response(topic: Topic) -> TopicResponse:
    response = TopicResponse.model_validate(topic)
    if not response.specialists and response.specialist:
        response.specialists = [response.specialist]
    return response


def _load_specialists(ids: list[int], db: Session) -> list[User]:
    if not ids:
        return []
    specialists = db.scalars(select(User).where(User.id.in_(ids), User.role == UserRole.specialist)).all()
    if len(specialists) != len(set(ids)):
        raise HTTPException(status_code=400, detail='Один или несколько специалистов не найдены')
    return specialists


@router.get('', response_model=list[TopicResponse])
def list_topics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TopicResponse]:
    stmt = select(Topic).options(joinedload(Topic.specialist), joinedload(Topic.specialists)).order_by(Topic.id.asc())
    if current_user.role == UserRole.specialist:
        stmt = stmt.where(
            (Topic.specialist_id == current_user.id)
            | (Topic.specialists.any(User.id == current_user.id))
        )
    topics = db.scalars(stmt).unique().all()
    return [_response(topic) for topic in topics]


@router.post('', response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(
    payload: TopicCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TopicResponse:
    _ = admin_user
    existing = db.scalar(select(Topic).where(func.lower(Topic.name) == payload.name.lower()))
    if existing:
        raise HTTPException(status_code=400, detail='Тема уже существует')

    specialists = _load_specialists(payload.specialist_ids, db)
    topic = Topic(
        name=payload.name,
        is_active=payload.is_active,
        specialist_id=specialists[0].id if specialists else None,
        specialists=specialists,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return _response(topic)


@router.patch('/{topic_id}', response_model=TopicResponse)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TopicResponse:
    _ = admin_user
    topic = db.execute(
        select(Topic).where(Topic.id == topic_id).options(joinedload(Topic.specialist), joinedload(Topic.specialists))
    ).unique().scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail='Тема не найдена')

    if payload.name is not None:
        duplicate = db.scalar(select(Topic).where(func.lower(Topic.name) == payload.name.lower(), Topic.id != topic_id))
        if duplicate:
            raise HTTPException(status_code=400, detail='Тема уже существует')
        topic.name = payload.name
    if payload.is_active is not None:
        topic.is_active = payload.is_active
    if 'specialist_ids' in payload.model_fields_set or 'specialist_id' in payload.model_fields_set:
        specialists = _load_specialists(payload.specialist_ids or [], db)
        topic.specialists = specialists
        topic.specialist_id = specialists[0].id if specialists else None

    db.add(topic)
    db.commit()
    db.refresh(topic)
    return _response(topic)


@router.delete('/{topic_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    _ = admin_user
    topic = db.scalar(select(Topic).where(Topic.id == topic_id))
    if not topic:
        raise HTTPException(status_code=404, detail='Тема не найдена')

    tickets_count = db.scalar(select(func.count(Ticket.id)).where(Ticket.topic_id == topic_id))
    if tickets_count:
        raise HTTPException(status_code=400, detail='Нельзя удалить тему, по которой уже есть заявки. Отключите активность темы.')

    db.delete(topic)
    db.commit()
