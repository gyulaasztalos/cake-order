"""Minimal i18n layer — externalized UI strings from day one.

Same pattern as the sibling app: per-locale dicts + a `t(key, locale)` lookup.
Dependency-free; can be swapped for gettext/Babel without touching call sites.
Hungarian is the default; English and German are selectable on the page.
Missing en/de keys fall back to Hungarian (visible → gets translated).
"""

from __future__ import annotations

from app.config import settings

# Keys are dotted, stable identifiers (never shown raw).
HU: dict[str, str] = {
    "app.title": "Anita Tortái — Tortarendelés",
    "app.tagline": "Cukrász manufaktúra — egyedi torták, szeretettel készítve",
    "app.language": "Nyelv",
    # form
    "form.title": "Tortarendelés",
    "form.intro": (
        "Írja le, milyen tortát szeretne, és hamarosan jelentkezünk egy személyre "
        "szabott ajánlattal."
    ),
    "form.name": "Név",
    "form.email": "E-mail cím",
    "form.email_hint": "Erre a címre küldjük a megerősítő linket.",
    "form.phone": "Telefonszám (nem kötelező)",
    "form.due_date": "Mikorra készüljön el?",
    "form.due_date_hint": "Legalább {days} nappal előre kérjük a rendelést.",
    "form.description": "Milyen tortát szeretne?",
    "form.description_hint": (
        "Alkalom, méret (hány szeletes), ízek, díszítés, minden ötlet érdekel! "
        "Legfeljebb {max} karakter."
    ),
    "form.consent": "Elfogadom az {link}t.",
    "form.consent_link": "adatkezelési tájékoztató",
    "form.submit": "Rendelés elküldése",
    # validation errors
    "error.name_required": "Kérjük, adja meg a nevét.",
    "error.email_invalid": "Kérjük, érvényes e-mail címet adjon meg.",
    "error.phone_invalid": "Kérjük, érvényes telefonszámot adjon meg.",
    "error.due_date_invalid": "Kérjük, válasszon dátumot.",
    "error.due_date_too_soon": "A megadott dátum túl közeli — legalább {days} nap szükséges.",
    "error.description_required": "Kérjük, írja le, milyen tortát szeretne.",
    "error.description_too_long": "A leírás túl hosszú (legfeljebb {max} karakter).",
    "error.consent_required": "A rendeléshez el kell fogadnia az adatkezelési tájékoztatót.",
    "error.too_fast": "Kérjük, próbálja újra elküldeni az űrlapot.",
    "error.rate_limited": "Túl sok próbálkozás. Kérjük, próbálja újra később.",
    "error.send_failed": "Az e-mail küldése nem sikerült. Kérjük, próbálja újra később.",
    # submitted page
    "submitted.title": "Már majdnem kész!",
    "submitted.body": (
        "Megerősítő e-mailt küldtünk a(z) {email} címre. A rendelés véglegesítéséhez "
        "kattintson az e-mailben található linkre. A link {hours} óráig érvényes."
    ),
    "submitted.spam_hint": "Ha nem találja a levelet, nézze meg a spam mappát is.",
    # verify pages
    "verified.title": "Köszönjük a rendelését!",
    "verified.body": (
        "A rendelését megkaptuk, és hamarosan felvesszük Önnel a kapcsolatot "
        "a részletekkel és az árajánlattal."
    ),
    "verify.already.title": "Ez a rendelés már megerősítve",
    "verify.already.body": "Ezt a rendelést korábban már megerősítette — nincs több teendője.",
    "verify.invalid.title": "Érvénytelen vagy lejárt link",
    "verify.invalid.body": (
        "Ez a megerősítő link érvénytelen vagy lejárt. Kérjük, adja fel a rendelését újra."
    ),
    "verify.back_home": "Vissza a rendeléshez",
    "verify.failed.title": "Nem sikerült továbbítani a rendelést",
    "verify.failed.body": (
        "Átmeneti hiba történt a rendelés továbbítása közben. A megerősítő link "
        "továbbra is érvényes — kérjük, próbálja meg pár perc múlva újra."
    ),
    "verify.failed.retry": "Újrapróbálás",
    # emails
    "email.verify.subject": "Erősítse meg tortarendelését — Anita Tortái",
    "email.verify.greeting": "Kedves {name}!",
    "email.verify.body": (
        "Köszönjük a rendelését! Kérjük, erősítse meg az e-mail címét az alábbi "
        "gombra kattintva, hogy továbbíthassuk a rendelést."
    ),
    "email.verify.button": "Rendelés megerősítése",
    "email.verify.link_hint": "Ha a gomb nem működik, másolja ezt a linket a böngészőbe:",
    "email.verify.expiry": "A link {hours} óráig érvényes.",
    "email.verify.ignore": "Ha nem Ön adta fel a rendelést, hagyja figyelmen kívül ezt a levelet.",
    "email.confirm.subject": "Rendelését megkaptuk — Anita Tortái",
    "email.confirm.greeting": "Kedves {name}!",
    "email.confirm.body": (
        "Köszönjük, rendelését megkaptuk! Hamarosan felvesszük Önnel a kapcsolatot "
        "a részletekkel és az árajánlattal."
    ),
    "email.confirm.summary": "A rendelés adatai",
    "email.chef.subject": "Új tortarendelés: {name} — {due_date}",
    "email.chef.title": "Új tortarendelés érkezett",
    "email.field.name": "Név",
    "email.field.email": "E-mail",
    "email.field.phone": "Telefon",
    "email.field.due_date": "Határidő",
    "email.field.description": "A torta leírása",
    "email.field.locale": "Nyelv",
    "email.footer": "Anita Tortái — anitatortai.hu",
    # privacy
    "privacy.title": "Adatkezelési tájékoztató",
    "nav.privacy": "Adatkezelés",
}

EN: dict[str, str] = {
    "app.title": "Anita Tortái — Cake Order",
    "app.tagline": "Artisan cake workshop — custom cakes, made with love",
    "app.language": "Language",
    "form.title": "Cake order",
    "form.intro": (
        "Tell us about the cake you would like, and we will get back to you "
        "with a personalised offer."
    ),
    "form.name": "Name",
    "form.email": "E-mail address",
    "form.email_hint": "We will send the confirmation link to this address.",
    "form.phone": "Phone number (optional)",
    "form.due_date": "When do you need it?",
    "form.due_date_hint": "Please order at least {days} days in advance.",
    "form.description": "What cake would you like?",
    "form.description_hint": (
        "Occasion, size (number of slices), flavours, decoration — every idea "
        "helps! At most {max} characters."
    ),
    "form.consent": "I accept the {link}.",
    "form.consent_link": "privacy notice",
    "form.submit": "Send order",
    "error.name_required": "Please enter your name.",
    "error.email_invalid": "Please enter a valid e-mail address.",
    "error.phone_invalid": "Please enter a valid phone number.",
    "error.due_date_invalid": "Please pick a date.",
    "error.due_date_too_soon": "That date is too soon — at least {days} days are needed.",
    "error.description_required": "Please describe the cake you would like.",
    "error.description_too_long": "The description is too long (at most {max} characters).",
    "error.consent_required": "You need to accept the privacy notice to order.",
    "error.too_fast": "Please try submitting the form again.",
    "error.rate_limited": "Too many attempts. Please try again later.",
    "error.send_failed": "Sending the e-mail failed. Please try again later.",
    "submitted.title": "Almost done!",
    "submitted.body": (
        "We have sent a confirmation e-mail to {email}. Click the link in it to "
        "finalise your order. The link is valid for {hours} hours."
    ),
    "submitted.spam_hint": "If you cannot find the e-mail, please check your spam folder.",
    "verified.title": "Thank you for your order!",
    "verified.body": (
        "We have received your order and will contact you soon with the details and a price offer."
    ),
    "verify.already.title": "This order is already confirmed",
    "verify.already.body": "You have already confirmed this order — nothing more to do.",
    "verify.invalid.title": "Invalid or expired link",
    "verify.invalid.body": (
        "This confirmation link is invalid or has expired. Please submit your order again."
    ),
    "verify.back_home": "Back to the order form",
    "verify.failed.title": "We could not pass your order on",
    "verify.failed.body": (
        "A temporary error occurred while forwarding your order. Your confirmation "
        "link is still valid — please try again in a few minutes."
    ),
    "verify.failed.retry": "Try again",
    "email.verify.subject": "Confirm your cake order — Anita Tortái",
    "email.verify.greeting": "Dear {name},",
    "email.verify.body": (
        "Thank you for your order! Please confirm your e-mail address by clicking "
        "the button below so we can pass your order on."
    ),
    "email.verify.button": "Confirm order",
    "email.verify.link_hint": "If the button does not work, copy this link into your browser:",
    "email.verify.expiry": "The link is valid for {hours} hours.",
    "email.verify.ignore": "If you did not place this order, simply ignore this e-mail.",
    "email.confirm.subject": "We received your order — Anita Tortái",
    "email.confirm.greeting": "Dear {name},",
    "email.confirm.body": (
        "Thank you, we have received your order! We will contact you soon with "
        "the details and a price offer."
    ),
    "email.confirm.summary": "Order details",
    "email.chef.subject": "New cake order: {name} — {due_date}",
    "email.chef.title": "A new cake order has arrived",
    "email.field.name": "Name",
    "email.field.email": "E-mail",
    "email.field.phone": "Phone",
    "email.field.due_date": "Due date",
    "email.field.description": "Cake description",
    "email.field.locale": "Language",
    "email.footer": "Anita Tortái — anitatortai.hu",
    "privacy.title": "Privacy notice",
    "nav.privacy": "Privacy",
}

DE: dict[str, str] = {
    "app.title": "Anita Tortái — Tortenbestellung",
    "app.tagline": "Tortenmanufaktur — individuelle Torten, mit Liebe gemacht",
    "app.language": "Sprache",
    "form.title": "Tortenbestellung",
    "form.intro": (
        "Beschreiben Sie die gewünschte Torte, und wir melden uns bald mit einem "
        "persönlichen Angebot."
    ),
    "form.name": "Name",
    "form.email": "E-Mail-Adresse",
    "form.email_hint": "An diese Adresse senden wir den Bestätigungslink.",
    "form.phone": "Telefonnummer (optional)",
    "form.due_date": "Wann wird die Torte benötigt?",
    "form.due_date_hint": "Bitte bestellen Sie mindestens {days} Tage im Voraus.",
    "form.description": "Welche Torte wünschen Sie sich?",
    "form.description_hint": (
        "Anlass, Größe (Anzahl der Stücke), Geschmack, Dekoration — jede Idee "
        "hilft! Höchstens {max} Zeichen."
    ),
    "form.consent": "Ich akzeptiere die {link}.",
    "form.consent_link": "Datenschutzerklärung",
    "form.submit": "Bestellung absenden",
    "error.name_required": "Bitte geben Sie Ihren Namen ein.",
    "error.email_invalid": "Bitte geben Sie eine gültige E-Mail-Adresse ein.",
    "error.phone_invalid": "Bitte geben Sie eine gültige Telefonnummer ein.",
    "error.due_date_invalid": "Bitte wählen Sie ein Datum.",
    "error.due_date_too_soon": (
        "Das Datum ist zu knapp — mindestens {days} Tage Vorlauf sind nötig."
    ),
    "error.description_required": "Bitte beschreiben Sie die gewünschte Torte.",
    "error.description_too_long": "Die Beschreibung ist zu lang (höchstens {max} Zeichen).",
    "error.consent_required": "Zur Bestellung müssen Sie die Datenschutzerklärung akzeptieren.",
    "error.too_fast": "Bitte senden Sie das Formular erneut ab.",
    "error.rate_limited": "Zu viele Versuche. Bitte versuchen Sie es später erneut.",
    "error.send_failed": "Der E-Mail-Versand ist fehlgeschlagen. Bitte versuchen Sie es später.",
    "submitted.title": "Fast geschafft!",
    "submitted.body": (
        "Wir haben eine Bestätigungs-E-Mail an {email} gesendet. Klicken Sie auf "
        "den Link darin, um Ihre Bestellung abzuschließen. Der Link ist {hours} "
        "Stunden gültig."
    ),
    "submitted.spam_hint": "Falls Sie die E-Mail nicht finden, prüfen Sie bitte den Spam-Ordner.",
    "verified.title": "Vielen Dank für Ihre Bestellung!",
    "verified.body": (
        "Wir haben Ihre Bestellung erhalten und melden uns bald mit den Details "
        "und einem Preisangebot."
    ),
    "verify.already.title": "Diese Bestellung ist bereits bestätigt",
    "verify.already.body": "Sie haben diese Bestellung bereits bestätigt — nichts weiter zu tun.",
    "verify.invalid.title": "Ungültiger oder abgelaufener Link",
    "verify.invalid.body": (
        "Dieser Bestätigungslink ist ungültig oder abgelaufen. Bitte geben Sie "
        "Ihre Bestellung erneut auf."
    ),
    "verify.back_home": "Zurück zur Bestellung",
    "verify.failed.title": "Ihre Bestellung konnte nicht weitergeleitet werden",
    "verify.failed.body": (
        "Beim Weiterleiten Ihrer Bestellung ist ein vorübergehender Fehler "
        "aufgetreten. Ihr Bestätigungslink ist weiterhin gültig — bitte versuchen "
        "Sie es in ein paar Minuten erneut."
    ),
    "verify.failed.retry": "Erneut versuchen",
    "email.verify.subject": "Bestätigen Sie Ihre Tortenbestellung — Anita Tortái",
    "email.verify.greeting": "Liebe(r) {name},",
    "email.verify.body": (
        "vielen Dank für Ihre Bestellung! Bitte bestätigen Sie Ihre E-Mail-Adresse "
        "über die Schaltfläche unten, damit wir Ihre Bestellung weiterleiten können."
    ),
    "email.verify.button": "Bestellung bestätigen",
    "email.verify.link_hint": (
        "Falls die Schaltfläche nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:"
    ),
    "email.verify.expiry": "Der Link ist {hours} Stunden gültig.",
    "email.verify.ignore": (
        "Falls Sie diese Bestellung nicht aufgegeben haben, ignorieren Sie diese E-Mail bitte."
    ),
    "email.confirm.subject": "Ihre Bestellung ist eingegangen — Anita Tortái",
    "email.confirm.greeting": "Liebe(r) {name},",
    "email.confirm.body": (
        "vielen Dank, Ihre Bestellung ist bei uns eingegangen! Wir melden uns bald "
        "mit den Details und einem Preisangebot."
    ),
    "email.confirm.summary": "Bestelldetails",
    "email.chef.subject": "Neue Tortenbestellung: {name} — {due_date}",
    "email.chef.title": "Eine neue Tortenbestellung ist eingegangen",
    "email.field.name": "Name",
    "email.field.email": "E-Mail",
    "email.field.phone": "Telefon",
    "email.field.due_date": "Termin",
    "email.field.description": "Tortenbeschreibung",
    "email.field.locale": "Sprache",
    "email.footer": "Anita Tortái — anitatortai.hu",
    "privacy.title": "Datenschutzerklärung",
    "nav.privacy": "Datenschutz",
}

CATALOGS: dict[str, dict[str, str]] = {"hu": HU, "en": EN, "de": DE}
SUPPORTED_LOCALES = tuple(CATALOGS)
LOCALE_NAMES = {"hu": "Magyar", "en": "English", "de": "Deutsch"}


def enabled_locales() -> tuple[str, ...]:
    """Locales that are both built (catalog exists) and enabled by config."""
    return tuple(code for code in settings.enabled_locales if code in CATALOGS)


def enabled_locale_names() -> dict[str, str]:
    return {code: LOCALE_NAMES[code] for code in enabled_locales()}


def resolve_locale(value: str | None) -> str:
    """Clamp any user-supplied locale to the ENABLED set (never trust input)."""
    return value if value in enabled_locales() else settings.default_locale


def t(key: str, locale: str | None = None, **kwargs: object) -> str:
    """Translate a key. Falls back to Hungarian, then the key itself (visible in dev)."""
    cat = CATALOGS.get(locale or settings.default_locale, HU)
    text = cat.get(key) or HU.get(key, key)
    return text.format(**kwargs) if kwargs else text
