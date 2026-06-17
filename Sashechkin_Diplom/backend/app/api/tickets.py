from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.topic import Topic
from app.models.user import User
from app.schemas.ticket import TicketResponse, TicketStatusUpdateRequest, TicketTakeRequest
from app.services.email import send_ticket_closed_email

router = APIRouter(prefix='/tickets', tags=['Tickets'])


def _can_specialist_access_topic(topic: Topic, user: User) -> bool:
    return topic.specialist_id == user.id or any(specialist.id == user.id for specialist in topic.specialists)


@router.get('', response_model=list[TicketResponse])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias='status'),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    stmt = (
        select(Ticket)
        .options(joinedload(Ticket.topic).joinedload(Topic.specialists), joinedload(Ticket.assigned_specialist))
        .order_by(Ticket.id.desc())
    )

    if current_user.role == UserRole.specialist:
        stmt = stmt.where(
            (Ticket.assigned_specialist_id == current_user.id)
            | (Ticket.topic.has(Topic.specialist_id == current_user.id))
            | (Ticket.topic.has(Topic.specialists.any(User.id == current_user.id)))
        )

    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)

    tickets = db.scalars(stmt).unique().all()
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


@router.get('/{ticket_id}', response_model=TicketResponse)
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TicketResponse:
    ticket = db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(joinedload(Ticket.topic).joinedload(Topic.specialists), joinedload(Ticket.assigned_specialist))
    ).unique().scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail='Заявка не найдена')

    if current_user.role == UserRole.specialist:
        if not _can_specialist_access_topic(ticket.topic, current_user) and ticket.assigned_specialist_id != current_user.id:
            raise HTTPException(status_code=403, detail='Нет доступа к заявке')

    return TicketResponse.model_validate(ticket)


@router.post('/{ticket_id}/take', response_model=TicketResponse)
def take_ticket(
    ticket_id: int,
    payload: TicketTakeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    _ = payload
    if current_user.role != UserRole.specialist:
        raise HTTPException(status_code=403, detail='Только для специалистов')

    ticket = db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(joinedload(Ticket.topic).joinedload(Topic.specialists), joinedload(Ticket.assigned_specialist))
    ).unique().scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail='Заявка не найдена')

    if ticket.status == TicketStatus.closed:
        raise HTTPException(status_code=400, detail='Закрытую заявку нельзя взять в работу')

    if not _can_specialist_access_topic(ticket.topic, current_user):
        raise HTTPException(status_code=403, detail='Эта заявка не из вашей темы')

    ticket.assigned_specialist_id = current_user.id
    ticket.status = TicketStatus.in_progress
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.post('/{ticket_id}/status', response_model=TicketResponse)
def update_status(
    ticket_id: int,
    payload: TicketStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    if payload.status == TicketStatus.new:
        raise HTTPException(status_code=400, detail='Нельзя вернуть в статус "Новая" этим методом')

    ticket = db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(joinedload(Ticket.topic).joinedload(Topic.specialists), joinedload(Ticket.assigned_specialist))
    ).unique().scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail='Заявка не найдена')

    if ticket.status == TicketStatus.closed:
        raise HTTPException(status_code=400, detail='Закрытую заявку нельзя возобновить')

    if current_user.role == UserRole.specialist:
        if ticket.assigned_specialist_id != current_user.id:
            raise HTTPException(status_code=403, detail='Вы не назначены на заявку')

    should_send_close_email = payload.status == TicketStatus.closed
    ticket.status = payload.status
    if payload.status == TicketStatus.closed:
        ticket.closed_at = datetime.now(timezone.utc)
    else:
        ticket.closed_at = None

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    if should_send_close_email:
        send_ticket_closed_email(ticket)

    return TicketResponse.model_validate(ticket)
