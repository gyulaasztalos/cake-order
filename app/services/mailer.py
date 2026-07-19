"""SMTP mailer + the three transactional e-mails (PLANNING §3.3).

Header-injection safe by construction: user input only ever goes into the
message BODY (Jinja-autoescaped for HTML) — never into header fields. The one
exception is the recipient address, which has passed email_validator. Sending
is synchronous (routes run in the threadpool); failures raise MailerError so
callers decide what the visitor sees.
"""

from __future__ import annotations

import smtplib
import ssl
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.config import settings
from app.i18n import t
from app.models import Order
from app.templating import email_env


class MailerError(Exception):
    """Sending failed; the caller chooses the user-facing consequence."""


def _render(template: str, **ctx: object) -> str:
    return email_env.get_template(f"email/{template}").render(**ctx)


def _build(to_addr: str, subject: str, text: str, html: str, reply_to: str | None = None):
    msg = EmailMessage()
    msg["From"] = str(Address("Anita Tortái", addr_spec=settings.mail_from))
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _send(msg: EmailMessage) -> None:
    try:
        if settings.smtp_security == "tls":
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, context=ssl.create_default_context()
            ) as smtp:
                _login_and_send(smtp, msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                if settings.smtp_security == "starttls":
                    smtp.starttls(context=ssl.create_default_context())
                _login_and_send(smtp, msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailerError(str(exc)) from exc


def _login_and_send(smtp: smtplib.SMTP, msg: EmailMessage) -> None:
    if settings.smtp_user:
        smtp.login(settings.smtp_user, settings.smtp_password)
    smtp.send_message(msg)


def send_verification(order: Order, verify_url: str) -> None:
    loc = order.locale
    ctx = {
        "locale": loc,
        "order": order,
        "verify_url": verify_url,
        "hours": settings.token_ttl_hours,
    }
    msg = _build(
        order.email,
        t("email.verify.subject", loc),
        _render("verify.txt", **ctx),
        _render("verify.html", **ctx),
    )
    _send(msg)


def send_order_to_chef(order: Order, offer_url: str | None = None) -> None:
    # Chef mail is always Hungarian regardless of the customer's language.
    ctx = {"locale": "hu", "order": order, "offer_url": offer_url}
    msg = _build(
        settings.order_inbox,
        t("email.chef.subject", "hu", name=order.name, due_date=order.due_date.isoformat()),
        _render("order_chef.txt", **ctx),
        _render("order_chef.html", **ctx),
        reply_to=order.email,
    )
    _send(msg)


def send_customer_confirmation(order: Order) -> None:
    loc = order.locale
    ctx = {"locale": loc, "order": order}
    msg = _build(
        order.email,
        t("email.confirm.subject", loc),
        _render("confirm.txt", **ctx),
        _render("confirm.html", **ctx),
    )
    _send(msg)
