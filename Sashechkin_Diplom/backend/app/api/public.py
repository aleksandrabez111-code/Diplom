from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.topic import Topic
from app.schemas.ticket import TicketCreatePublic, TicketCreatePublicResponse
from app.schemas.topic import TopicPublic

router = APIRouter(prefix='/public', tags=['Public'])


@router.get('/topics', response_model=list[TopicPublic])
def get_public_topics(db: Session = Depends(get_db)) -> list[TopicPublic]:
    topics = db.scalars(select(Topic).where(Topic.is_active.is_(True)).order_by(Topic.name.asc())).all()
    return [TopicPublic.model_validate(topic) for topic in topics]


@router.post('/tickets', response_model=TicketCreatePublicResponse, status_code=status.HTTP_201_CREATED)
def create_public_ticket(payload: TicketCreatePublic, db: Session = Depends(get_db)) -> TicketCreatePublicResponse:
    topic = db.execute(
        select(Topic)
        .where(Topic.id == payload.topic_id)
        .options(joinedload(Topic.specialist), joinedload(Topic.specialists))
    ).unique().scalar_one_or_none()
    if not topic or not topic.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тема недоступна')

    active_specialists = [
        specialist
        for specialist in topic.specialists
        if specialist.is_active and specialist.role == UserRole.specialist
    ]
    if not active_specialists and topic.specialist and topic.specialist.is_active and topic.specialist.role == UserRole.specialist:
        active_specialists = [topic.specialist]

    assigned_specialist_id = active_specialists[0].id if active_specialists else None

    ticket = Ticket(
        ticket_number='TMP',
        topic_id=topic.id,
        message_text=payload.message_text,
        contact_email=payload.contact_email,
        status=TicketStatus.new,
        assigned_specialist_id=assigned_specialist_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ticket)
    db.flush()

    ticket.ticket_number = f'TKT-{ticket.id:05d}'
    db.add(ticket)
    db.commit()

    return TicketCreatePublicResponse(id=ticket.id, ticket_number=ticket.ticket_number, message='Обращение отправлено')
