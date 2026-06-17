from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path
import smtplib

from app.core.config import settings
from app.models.ticket import Ticket


def _from_address() -> Address | str:
    email = settings.smtp_from_email or settings.smtp_username
    if not email:
        return 'no-reply@localhost'

    if '@' not in email:
        return email

    username, domain = email.split('@', 1)
    return Address(display_name=settings.smtp_from_name, username=username, domain=domain)


def _from_domain() -> str:
    email = settings.smtp_from_email or settings.smtp_username
    if '@' not in email:
        return 'localhost'
    return email.split('@', 1)[1]


def _closed_ticket_message(ticket: Ticket) -> EmailMessage:
    message = EmailMessage()
    message['Subject'] = f'Обращение {ticket.ticket_number} обработано'
    message['From'] = _from_address()
    message['To'] = ticket.contact_email
    message['Date'] = formatdate(localtime=True)
    message['Message-ID'] = make_msgid(domain=_from_domain())
    message['Auto-Submitted'] = 'auto-generated'
    message['X-Auto-Response-Suppress'] = 'All'
    if settings.smtp_from_name:
        message['Organization'] = settings.smtp_from_name
    if settings.smtp_from_email:
        message['Reply-To'] = settings.smtp_from_email

    topic_name = ticket.topic.name if ticket.topic else 'обращение'
    body = (
        f'Здравствуйте.\n\n'
        f'Ваше обращение {ticket.ticket_number} по теме "{topic_name}" обработано и закрыто специалистом.\n\n'
        f'Если вопрос сохранится, пожалуйста, создайте новое обращение через страницу приема заявок '
        f'или ответьте на это письмо.\n\n'
        f'Это автоматическое уведомление о результате обработки обращения.\n\n'
        f'С уважением,\n'
        f'{settings.smtp_from_name}\n'
    )
    message.set_content(body, charset='utf-8', cte='quoted-printable')
    return message


def _outbox_dir() -> Path:
    outbox_dir = Path(settings.email_outbox_dir)
    if not outbox_dir.is_absolute():
        outbox_dir = Path.cwd() / outbox_dir
    outbox_dir.mkdir(parents=True, exist_ok=True)
    return outbox_dir


def _format_smtp_error(error: Exception) -> str:
    if isinstance(error, smtplib.SMTPResponseException):
        message = error.smtp_error
        if isinstance(message, bytes):
            message = message.decode('utf-8', errors='replace')
        return f'{type(error).__name__}: {error.smtp_code} {message}'

    if isinstance(error, smtplib.SMTPRecipientsRefused):
        refused = []
        for email, value in error.recipients.items():
            code, message = value
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            refused.append(f'{email}: {code} {message}')
        return f'{type(error).__name__}: ' + '; '.join(refused)

    return f'{type(error).__name__}: {error}'


def _write_to_outbox(message: EmailMessage, ticket: Ticket, error: Exception | None = None, reason: str | None = None) -> None:
    outbox_dir = _outbox_dir()
    filename = outbox_dir / f'{ticket.ticket_number}_closed.eml'
    filename.write_text(message.as_string(), encoding='utf-8')

    if error or reason:
        details = reason or _format_smtp_error(error)
        error_filename = outbox_dir / f'{ticket.ticket_number}_smtp_error.txt'
        error_filename.write_text(details, encoding='utf-8')


def send_ticket_closed_email(ticket: Ticket) -> None:
    message = _closed_ticket_message(ticket)

    if not settings.smtp_enabled or not settings.smtp_host:
        _write_to_outbox(message, ticket, reason='SMTP отключен или не указан SMTP_HOST.')
        return

    try:
        if settings.smtp_use_ssl:
            smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds)
        else:
            smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds)

        with smtp:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message, from_addr=settings.smtp_from_email or settings.smtp_username, to_addrs=[ticket.contact_email])
    except Exception as exc:
        _write_to_outbox(message, ticket, error=exc)
        print(f'Не удалось отправить письмо по SMTP: {type(exc).__name__}: {exc}')
