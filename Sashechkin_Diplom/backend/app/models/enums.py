from enum import Enum


class UserRole(str, Enum):
    admin = 'admin'
    specialist = 'specialist'


class TicketStatus(str, Enum):
    new = 'new'
    in_progress = 'in_progress'
    closed = 'closed'
