from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TicketStatus
from app.schemas.topic import TopicPublic
from app.schemas.user import UserShort


class TicketCreatePublic(BaseModel):
    topic_id: int
    message_text: str = Field(min_length=5, max_length=3000)
    contact_email: EmailStr


class TicketCreatePublicResponse(BaseModel):
    id: int
    ticket_number: str
    message: str


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    topic: TopicPublic
    message_text: str
    contact_email: EmailStr
    status: TicketStatus
    assigned_specialist: UserShort | None = None
    created_at: datetime
    closed_at: datetime | None = None

    model_config = {'from_attributes': True}


class TicketTakeRequest(BaseModel):
    pass


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus
