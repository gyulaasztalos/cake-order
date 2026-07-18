"""Order intake flow: bot defenses, validation, verification, e-mails."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient

from app.main import app
from app.services.security import issue_form_token

client = TestClient(app)

VALID_DUE = (dt.date.today() + dt.timedelta(days=14)).isoformat()


def _form(**overrides) -> dict[str, str]:
    base = {
        "name": "Kovács Éva",
        "email": "eva@example.com",
        "phone": "+36 30 123 4567",
        "due_date": VALID_DUE,
        "cake_type": "birthday",
        "flavor": "oreo",
        "portions": "16",
        "description": (
            "16 szeletes epres torta, vintage szív díszítéssel. Írás: „Boldog szülinapot”"
        ),
        "consent": "true",
        "form_token": issue_form_token(),
        "website": "",
    }
    base.update(overrides)
    return base


# --- DB-free: bot defenses + validation --------------------------------------


def test_honeypot_gets_fake_success_and_sends_nothing(outbox):
    r = client.post("/ajanlatkeres", data=_form(website="http://spam.example"))
    assert r.status_code == 200
    assert outbox == []


def test_instant_submit_is_rejected(outbox):
    # Default MIN_FILL_SECONDS=3; a token issued "now" means a sub-second fill.
    r = client.post("/ajanlatkeres", data=_form())
    assert r.status_code == 400
    assert outbox == []


def test_forged_form_token_is_rejected(fast_form, outbox):
    forged = "12345.deadbeef"  # noqa: S105 — not a secret, an invalid signature
    r = client.post("/ajanlatkeres", data=_form(form_token=forged))
    assert r.status_code == 400
    assert outbox == []


def test_validation_errors_rerender_form(fast_form, outbox):
    r = client.post(
        "/ajanlatkeres",
        data=_form(name="", email="not-an-email", due_date="2020-01-01", description=""),
    )
    assert r.status_code == 422
    assert outbox == []


def test_description_xss_is_escaped_on_rerender(fast_form):
    evil = "<script>alert(1)</script><img src=x onerror=alert(2)>"
    r = client.post("/ajanlatkeres", data=_form(email="broken", description=evil))
    assert r.status_code == 422
    assert "<script>alert(1)" not in r.text
    assert evil not in r.text  # autoescaped, but the visitor's text is preserved
    assert "&lt;script&gt;" in r.text


def test_consent_is_mandatory(fast_form):
    r = client.post("/ajanlatkeres", data=_form(consent=""))
    assert r.status_code == 422


# --- DB-backed: happy path + verification ------------------------------------


def _submit_ok(outbox) -> str:
    """Submit a valid order; return the raw verification token from the e-mail."""
    r = client.post("/ajanlatkeres", data=_form())
    assert r.status_code == 200, r.text
    assert len(outbox) == 1
    body = outbox[0].get_body(("plain",)).get_content()
    link = next(line for line in body.splitlines() if "/verify/" in line)
    return link.rsplit("/verify/", 1)[1].strip()


def test_happy_path_submit_then_verify(clean_db, fast_form, outbox):
    token = _submit_ok(outbox)

    r = client.get(f"/verify/{token}")
    assert r.status_code == 200
    # chef order mail + customer confirmation went out after verification
    assert len(outbox) == 3
    chef_msg, confirm_msg = outbox[1], outbox[2]
    assert chef_msg["To"] == "info@anitatortai.hu"
    assert chef_msg["Reply-To"] == "eva@example.com"
    chef_text = chef_msg.get_body(("plain",)).get_content()
    assert "Kovács Éva" in chef_text
    assert "Oreo" in chef_text  # flavor choice reaches the chef
    assert "Születésnapi torta" in chef_text
    assert confirm_msg["To"] == "eva@example.com"

    from app.db import SessionLocal
    from app.models import Order

    s = SessionLocal()
    try:
        order = s.query(Order).one()
        assert order.status == "confirmed"
        assert order.verified_at is not None
    finally:
        s.close()


def test_verify_link_is_single_use(clean_db, fast_form, outbox):
    token = _submit_ok(outbox)
    assert client.get(f"/verify/{token}").status_code == 200
    # Second click: friendly "already confirmed", no more e-mails.
    r = client.get(f"/verify/{token}")
    assert r.status_code == 200
    assert len(outbox) == 3


def test_verify_with_unknown_token_404s(clean_db):
    assert client.get("/verify/definitely-not-a-token").status_code == 404


def test_resubmit_same_email_refreshes_pending_order(clean_db, fast_form, outbox):
    token1 = _submit_ok(outbox)
    r = client.post("/ajanlatkeres", data=_form(description="Mégis csokitorta legyen!"))
    assert r.status_code == 200

    from app.db import SessionLocal
    from app.models import Order

    s = SessionLocal()
    try:
        order = s.query(Order).one()  # still exactly one row for this e-mail
        assert "csokitorta" in order.description
    finally:
        s.close()
    # The first link was invalidated by the refresh.
    assert client.get(f"/verify/{token1}").status_code == 404


def test_rate_limit_per_email(clean_db, fast_form, outbox, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rate_max_per_email", 2)
    monkeypatch.setattr(settings, "rate_max_per_ip", 100)
    assert client.post("/ajanlatkeres", data=_form()).status_code == 200
    assert client.post("/ajanlatkeres", data=_form()).status_code == 200
    assert client.post("/ajanlatkeres", data=_form()).status_code == 429


def test_chef_mail_failure_keeps_token_valid(clean_db, fast_form, outbox, monkeypatch):
    token = _submit_ok(outbox)

    from app.services import mailer

    def boom(msg):
        raise mailer.MailerError("smtp down")

    monkeypatch.setattr(mailer, "_send", boom)
    assert client.get(f"/verify/{token}").status_code == 502

    # SMTP recovers → the same link still works.
    monkeypatch.setattr(mailer, "_send", outbox.append)
    assert client.get(f"/verify/{token}").status_code == 200
