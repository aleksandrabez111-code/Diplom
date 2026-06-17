from sqlalchemy import ForeignKey, Table, Column, Integer

from app.models.base import Base


topic_specialists = Table(
    'topic_specialists',
    Base.metadata,
    Column('topic_id', Integer, ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
)
