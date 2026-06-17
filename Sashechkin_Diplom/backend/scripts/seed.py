from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.topic import Topic
from app.models.user import User


DEMO_USERS = [
    {
        'username': 'admin',
        'password': 'admin12345',
        'full_name': 'Администратор',
        'email': 'admin@support.example.com',
        'role': UserRole.admin,
    },
    {
        'username': 'spec1',
        'password': 'spec12345',
        'full_name': 'Иванов Иван',
        'email': 'spec1@support.example.com',
        'role': UserRole.specialist,
    },
    {
        'username': 'spec2',
        'password': 'spec12345',
        'full_name': 'Петров Петр',
        'email': 'spec2@support.example.com',
        'role': UserRole.specialist,
    },
]

DEMO_TOPICS = [
    {'name': 'Полис ОМС', 'specialists': ['spec1']},
    {'name': 'Прикрепление к поликлинике', 'specialists': ['spec1']},
    {'name': 'Техническая проблема сайта', 'specialists': ['spec2']},
]


def seed() -> None:
    db = SessionLocal()
    try:
        users_by_username: dict[str, User] = {}
        for item in DEMO_USERS:
            user = db.scalar(select(User).where(User.username == item['username']))
            if user is None:
                user = User(
                    username=item['username'],
                    password_hash=get_password_hash(item['password']),
                    full_name=item['full_name'],
                    email=item['email'],
                    role=item['role'],
                    is_active=True,
                )
                db.add(user)
                db.flush()
            else:
                user.full_name = item['full_name']
                user.email = item['email']
                user.role = item['role']
                user.is_active = True
            users_by_username[item['username']] = user

        for item in DEMO_TOPICS:
            specialists = [users_by_username[username] for username in item['specialists']]
            topic = db.scalar(select(Topic).where(Topic.name == item['name']))
            if topic is None:
                topic = Topic(
                    name=item['name'],
                    is_active=True,
                    specialist_id=specialists[0].id if specialists else None,
                    specialists=specialists,
                )
                db.add(topic)
            else:
                topic.is_active = True
                topic.specialist_id = specialists[0].id if specialists else None
                topic.specialists = specialists

        db.commit()
        print('Seed успешно применен')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
