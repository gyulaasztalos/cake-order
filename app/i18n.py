"""Minimal i18n layer — externalized UI strings from day one.

Same pattern as the sibling app: per-locale dicts + a `t(key, locale)` lookup.
Dependency-free; can be swapped for gettext/Babel without touching call sites.
Hungarian is the default; English and German are selectable on the page.
Missing en/de keys fall back to Hungarian (visible → gets translated).

Voice (owner decision, 2026-07-18): Hungarian uses TEGEZŐDÉS, and the chef
speaks in first person ("felveszem veled a kapcsolatot"). The customer submits
an AJÁNLATKÉRÉS (offer request) — never "rendelés"/"megrendelés" on the UI.
"""

from __future__ import annotations

from app.config import settings

# Keys are dotted, stable identifiers (never shown raw).
HU: dict[str, str] = {
    "app.title": "Anita Tortái — Ajánlatkérés",
    "app.tagline": "szeretetből sütve",
    "app.language": "Nyelv",
    # nav + footer
    "nav.home": "Főoldal",
    "nav.cakes": "Torták",
    "nav.desserts": "Desszertek",
    "nav.about": "Rólam",
    "nav.offer": "Ajánlatkérés",
    "nav.contact": "Kapcsolat",
    "nav.privacy": "Adatkezelési tájékoztató",
    "footer.blurb": "Egyedi, kézzel készített torták Szentendrén és környékén.",
    "footer.contact": "Kapcsolat",
    "footer.info": "Információk",
    "footer.offer_hint": "Vagy vedd fel velem a kapcsolatot üzenetben!",
    "footer.rights": "Minden jog fenntartva.",
    # landing / hero
    "hero.title": "Egyedi, kézzel készített torták",
    "hero.location": "Szentendrén és környékén.",
    "hero.body": "Minden torta egy történet, amit együtt alkotunk meg.",
    "hero.cta": "Ajánlatot kérek",
    "hero.cta_gallery": "Megnézem a tortákat",
    # why-me cards
    "why.title": "Miért válassz engem?",
    "why.handmade.title": "Kézzel készített dekorációk",
    "why.handmade.body": "Minden részlet gondosan, kézzel készül.",
    "why.premium.title": "Prémium alapanyagok",
    "why.premium.body": "Csak minőségi alapanyagokkal dolgozom.",
    "why.custom.title": "Egyedi tervezés",
    "why.custom.body": "A te elképzelésed alapján születik meg.",
    "why.love.title": "Szeretetből sütve",
    "why.love.body": "Minden tortába szívemet-lelkemet beleadom.",
    # how it works
    "steps.title": "Hogyan működik?",
    "steps.1.title": "Ajánlatkérés",
    "steps.1.body": "Töltsd ki az űrlapot, írd le az elképzeléseidet.",
    "steps.2.title": "Egyeztetés",
    "steps.2.body": "Felveszem veled a kapcsolatot, és egyeztetjük a részleteket.",
    "steps.3.title": "Elkészítés",
    "steps.3.body": "Szívvel-lélekkel elkészítem a te egyedi tortádat.",
    "steps.4.title": "Átvétel",
    "steps.4.body": "Átveszed a tortát, és jöhet az ünneplés!",
    # gallery
    "gallery.title": "Torták",
    "gallery.preview_title": "Néhány korábbi munkám",
    "gallery.all": "Összes torta megnézése",
    "gallery.desserts_title": "Desszertek",
    "gallery.placeholder_note": "A képek hamarosan érkeznek — addig is kérj bátran ajánlatot!",
    # about
    "about.title": "Rólam",
    "about.body1": (
        "Szia! Anita vagyok, az Anita Tortái cukrász manufaktúra megálmodója. "
        "Szentendrén és környékén készítek egyedi, kézzel díszített tortákat "
        "születésnapokra, esküvőkre és minden különleges alkalomra."
    ),
    "about.body2": (
        "Számomra minden torta egy történet: a tiéd. Meghallgatom az elképzelésed, "
        "és szívvel-lélekkel, prémium alapanyagokból alkotom meg — szeretetből sütve."
    ),
    "about.cta": "Kérj tőlem ajánlatot!",
    # contact
    "contact.title": "Kapcsolat",
    "contact.body": "Kérdésed van, vagy egyeztetnél? Írj bátran!",
    "contact.email": "E-mail",
    "contact.area": "Szentendre és környéke",
    "contact.area_label": "Átvétel",
    "contact.area_note": "Átvétel előre egyeztetett időpontban.",
    # offer form
    "form.title": "Ajánlatkérés",
    "form.intro": "Töltsd ki az űrlapot, és rövid időn belül felveszem veled a kapcsolatot!",
    "form.name": "Név",
    "form.name_ph": "Add meg a neved",
    "form.email": "E-mail cím",
    "form.email_ph": "Add meg az e-mail címed",
    "form.email_hint": "Erre a címre küldjük a megerősítő linket.",
    "form.phone": "Telefonszám",
    "form.phone_ph": "Add meg a telefonszámod",
    "form.optional": "nem kötelező",
    "form.due_date": "Esemény időpontja",
    "form.due_date_hint": "Legalább {days} nappal előre kérjük az ajánlatkérést.",
    "form.cake_type": "Torta típusa / téma",
    "form.cake_type_ph": "Válassz a lehetőségek közül",
    "form.cake_type.birthday": "Születésnapi torta",
    "form.cake_type.kids": "Gyerektorta",
    "form.cake_type.wedding": "Esküvői torta",
    "form.cake_type.shaped": "Formatorta",
    "form.cake_type.dessert": "Desszertek",
    "form.cake_type.other": "Egyéb",
    "form.portions": "Torta szeletek száma",
    "form.portions_ph": "Pl. 12 szelet",
    "form.flavor": "Íz",
    "form.flavor_hint": "ha már van ötleted",
    "form.flavor_ph": "Válassz ízt",
    "form.flavor.kinder": "Kinder",
    "form.flavor.kinder_maxi_king": "Kinder Maxi King",
    "form.flavor.oreo": "Oreo",
    "form.flavor.raffaello": "Raffaello",
    "form.flavor.csoki": "Csoki",
    "form.flavor.vanilia": "Vanília",
    "form.flavor.gesztenye": "Gesztenye",
    "form.flavor.tejszines_gyumolcsos": "Tejszínes gyümölcsös (eper, áfonya, málna stb.)",
    "form.flavor.karamella": "Karamella",
    "form.flavor.sos_karamell": "Sós karamell",
    "form.flavor.turo": "Túró",
    "form.flavor.dio": "Dió",
    "form.flavor.fehercsoki": "Fehércsoki",
    "form.flavor.oroszkrem": "Oroszkrém",
    "form.flavor.citrom": "Citrom",
    "form.flavor.pisztacia": "Pisztácia",
    "form.flavor.egyeb": "Egyéb",
    "form.description": "Egyéb kérések / megjegyzés",
    "form.description_ph": "Írd le kérlek, mit képzeltél el…",
    "form.description_hint": (
        "Alkalom, ízek, díszítés, felirat — minden ötlet érdekel! Legfeljebb {max} karakter."
    ),
    "form.consent": "Elfogadom az {link}t.",
    "form.consent_link": "adatkezelési tájékoztató",
    "form.submit": "Ajánlatkérés elküldése",
    # validation errors
    "error.name_required": "Kérlek, add meg a neved.",
    "error.email_invalid": "Kérlek, érvényes e-mail címet adj meg.",
    "error.phone_invalid": "Kérlek, érvényes telefonszámot adj meg.",
    "error.due_date_invalid": "Kérlek, válassz dátumot.",
    "error.due_date_too_soon": "A megadott dátum túl közeli — legalább {days} nap szükséges.",
    "error.cake_type_required": "Kérlek, válassz torta típust.",
    "error.portions_invalid": "Kérlek, valós szeletszámot adj meg.",
    "error.description_required": "Kérlek, írd le, mit képzeltél el.",
    "error.description_too_long": "A leírás túl hosszú (legfeljebb {max} karakter).",
    "error.consent_required": "Az ajánlatkéréshez el kell fogadnod az adatkezelési tájékoztatót.",
    "error.too_fast": "Kérlek, próbáld újra elküldeni az űrlapot.",
    "error.rate_limited": "Túl sok próbálkozás. Kérlek, próbáld újra később.",
    "error.send_failed": "Az e-mail küldése nem sikerült. Kérlek, próbáld újra később.",
    # submitted page
    "submitted.title": "Már majdnem kész!",
    "submitted.body": (
        "Megerősítő e-mailt küldtünk a(z) {email} címre. Az ajánlatkérés "
        "véglegesítéséhez kattints az e-mailben található linkre. A link {hours} "
        "óráig érvényes."
    ),
    "submitted.spam_hint": "Ha nem találod a levelet, nézd meg a spam mappát is.",
    # verify pages
    "verified.title": "Köszönöm az ajánlatkérésed!",
    "verified.body": (
        "Megkaptam az ajánlatkérésed, és hamarosan felveszem veled a kapcsolatot "
        "a részletekkel és az árajánlattal."
    ),
    "verify.already.title": "Ez az ajánlatkérés már megerősítve",
    "verify.already.body": "Ezt az ajánlatkérést korábban már megerősítetted — nincs több teendőd.",
    "verify.invalid.title": "Érvénytelen vagy lejárt link",
    "verify.invalid.body": (
        "Ez a megerősítő link érvénytelen vagy lejárt. Kérlek, add fel az ajánlatkérést újra."
    ),
    "verify.back_home": "Vissza a főoldalra",
    "verify.failed.title": "Nem sikerült továbbítani az ajánlatkérést",
    "verify.failed.body": (
        "Átmeneti hiba történt az ajánlatkérés továbbítása közben. A megerősítő "
        "link továbbra is érvényes — kérlek, próbáld meg pár perc múlva újra."
    ),
    "verify.failed.retry": "Újrapróbálás",
    # emails
    "email.verify.subject": "Erősítsd meg az ajánlatkérésed — Anita Tortái",
    "email.verify.greeting": "Kedves {name}!",
    "email.verify.body": (
        "Köszönöm az ajánlatkérésed! Kérlek, erősítsd meg az e-mail címed az "
        "alábbi gombra kattintva, hogy megkaphassam az üzeneted."
    ),
    "email.verify.button": "Ajánlatkérés megerősítése",
    "email.verify.link_hint": "Ha a gomb nem működik, másold ezt a linket a böngésződbe:",
    "email.verify.expiry": "A link {hours} óráig érvényes.",
    "email.verify.ignore": "Ha nem te kérted az ajánlatot, hagyd figyelmen kívül ezt a levelet.",
    "email.confirm.subject": "Megkaptam az ajánlatkérésed — Anita Tortái",
    "email.confirm.greeting": "Kedves {name}!",
    "email.confirm.body": (
        "Köszönöm, az ajánlatkérésed megérkezett! Hamarosan felveszem veled a "
        "kapcsolatot a részletekkel és az árajánlattal."
    ),
    "email.confirm.summary": "Az ajánlatkérés adatai",
    "email.chef.subject": "Új ajánlatkérés: {name} — {due_date}",
    "email.chef.title": "Új ajánlatkérés érkezett",
    "email.field.name": "Név",
    "email.field.email": "E-mail",
    "email.field.phone": "Telefon",
    "email.field.due_date": "Esemény időpontja",
    "email.field.cake_type": "Torta típusa",
    "email.field.flavor": "Íz",
    "email.field.portions": "Szeletek száma",
    "email.field.description": "Egyéb kérések",
    "email.field.locale": "Nyelv",
    "email.footer": "Anita Tortái — szeretetből sütve · anitatortai.hu",
    # privacy
    "privacy.title": "Adatkezelési tájékoztató",
}

EN: dict[str, str] = {
    "app.title": "Anita Tortái — Request an Offer",
    "app.tagline": "baked with love",
    "app.language": "Language",
    "nav.home": "Home",
    "nav.cakes": "Cakes",
    "nav.desserts": "Desserts",
    "nav.about": "About me",
    "nav.offer": "Request an offer",
    "nav.contact": "Contact",
    "nav.privacy": "Privacy notice",
    "footer.blurb": "Custom, handcrafted cakes in and around Szentendre.",
    "footer.contact": "Contact",
    "footer.info": "Information",
    "footer.offer_hint": "Or simply drop me a message!",
    "footer.rights": "All rights reserved.",
    "hero.title": "Custom, handcrafted cakes",
    "hero.location": "in and around Szentendre.",
    "hero.body": "Every cake is a story we create together.",
    "hero.cta": "Request an offer",
    "hero.cta_gallery": "See the cakes",
    "why.title": "Why choose me?",
    "why.handmade.title": "Handcrafted decorations",
    "why.handmade.body": "Every detail is carefully made by hand.",
    "why.premium.title": "Premium ingredients",
    "why.premium.body": "I only work with quality ingredients.",
    "why.custom.title": "Custom design",
    "why.custom.body": "Born from your very own idea.",
    "why.love.title": "Baked with love",
    "why.love.body": "I put my heart and soul into every cake.",
    "steps.title": "How does it work?",
    "steps.1.title": "Offer request",
    "steps.1.body": "Fill in the form and describe your ideas.",
    "steps.2.title": "Consultation",
    "steps.2.body": "I contact you and we agree on the details.",
    "steps.3.title": "Creation",
    "steps.3.body": "I craft your unique cake with heart and soul.",
    "steps.4.title": "Pickup",
    "steps.4.body": "You pick up the cake — let the celebration begin!",
    "gallery.title": "Cakes",
    "gallery.preview_title": "Some of my previous work",
    "gallery.all": "See all cakes",
    "gallery.desserts_title": "Desserts",
    "gallery.placeholder_note": (
        "Photos are coming soon — meanwhile, feel free to request an offer!"
    ),
    "about.title": "About me",
    "about.body1": (
        "Hi! I'm Anita, the founder of the Anita Tortái artisan cake workshop. "
        "I create custom, hand-decorated cakes in and around Szentendre for "
        "birthdays, weddings and every special occasion."
    ),
    "about.body2": (
        "For me every cake is a story: yours. I listen to your idea and create it "
        "with heart and soul, from premium ingredients — baked with love."
    ),
    "about.cta": "Request an offer from me!",
    "contact.title": "Contact",
    "contact.body": "Questions, or want to discuss an idea? Just write!",
    "contact.email": "E-mail",
    "contact.area": "Szentendre and surroundings",
    "contact.area_label": "Pickup",
    "contact.area_note": "Pickup at a pre-agreed time.",
    "form.title": "Request an offer",
    "form.intro": "Fill in the form and I will get back to you shortly!",
    "form.name": "Name",
    "form.name_ph": "Enter your name",
    "form.email": "E-mail address",
    "form.email_ph": "Enter your e-mail address",
    "form.email_hint": "We will send the confirmation link to this address.",
    "form.phone": "Phone number",
    "form.phone_ph": "Enter your phone number",
    "form.optional": "optional",
    "form.due_date": "Date of the event",
    "form.due_date_hint": "Please request your offer at least {days} days in advance.",
    "form.cake_type": "Cake type / theme",
    "form.cake_type_ph": "Choose from the options",
    "form.cake_type.birthday": "Birthday cake",
    "form.cake_type.kids": "Kids' cake",
    "form.cake_type.wedding": "Wedding cake",
    "form.cake_type.shaped": "Shaped cake",
    "form.cake_type.dessert": "Desserts",
    "form.cake_type.other": "Other",
    "form.portions": "Number of slices",
    "form.portions_ph": "E.g. 12 slices",
    "form.flavor": "Flavour",
    "form.flavor_hint": "if you already have an idea",
    "form.flavor_ph": "Choose a flavour",
    "form.flavor.csoki": "Chocolate",
    "form.flavor.vanilia": "Vanilla",
    "form.flavor.gesztenye": "Chestnut",
    "form.flavor.tejszines_gyumolcsos": "Creamy fruit (strawberry, blueberry, raspberry etc.)",
    "form.flavor.karamella": "Caramel",
    "form.flavor.sos_karamell": "Salted caramel",
    "form.flavor.turo": "Sweet curd cheese (túró)",
    "form.flavor.dio": "Walnut",
    "form.flavor.fehercsoki": "White chocolate",
    "form.flavor.oroszkrem": "Russian cream (oroszkrém)",
    "form.flavor.citrom": "Lemon",
    "form.flavor.pisztacia": "Pistachio",
    "form.flavor.egyeb": "Other",
    "form.description": "Other requests / notes",
    "form.description_ph": "Please describe what you have in mind…",
    "form.description_hint": (
        "Occasion, flavours, decoration, inscription — every idea helps! At most {max} characters."
    ),
    "form.consent": "I accept the {link}.",
    "form.consent_link": "privacy notice",
    "form.submit": "Send offer request",
    "error.name_required": "Please enter your name.",
    "error.email_invalid": "Please enter a valid e-mail address.",
    "error.phone_invalid": "Please enter a valid phone number.",
    "error.due_date_invalid": "Please pick a date.",
    "error.due_date_too_soon": "That date is too soon — at least {days} days are needed.",
    "error.cake_type_required": "Please choose a cake type.",
    "error.portions_invalid": "Please enter a realistic number of slices.",
    "error.description_required": "Please describe what you have in mind.",
    "error.description_too_long": "The description is too long (at most {max} characters).",
    "error.consent_required": "You need to accept the privacy notice to send a request.",
    "error.too_fast": "Please try submitting the form again.",
    "error.rate_limited": "Too many attempts. Please try again later.",
    "error.send_failed": "Sending the e-mail failed. Please try again later.",
    "submitted.title": "Almost done!",
    "submitted.body": (
        "We have sent a confirmation e-mail to {email}. Click the link in it to "
        "finalise your offer request. The link is valid for {hours} hours."
    ),
    "submitted.spam_hint": "If you cannot find the e-mail, please check your spam folder.",
    "verified.title": "Thank you for your request!",
    "verified.body": (
        "I have received your offer request and will contact you soon with the "
        "details and a price offer."
    ),
    "verify.already.title": "This request is already confirmed",
    "verify.already.body": "You have already confirmed this offer request — nothing more to do.",
    "verify.invalid.title": "Invalid or expired link",
    "verify.invalid.body": (
        "This confirmation link is invalid or has expired. Please submit your request again."
    ),
    "verify.back_home": "Back to the home page",
    "verify.failed.title": "We could not pass your request on",
    "verify.failed.body": (
        "A temporary error occurred while forwarding your offer request. Your "
        "confirmation link is still valid — please try again in a few minutes."
    ),
    "verify.failed.retry": "Try again",
    "email.verify.subject": "Confirm your offer request — Anita Tortái",
    "email.verify.greeting": "Dear {name},",
    "email.verify.body": (
        "Thank you for your offer request! Please confirm your e-mail address by "
        "clicking the button below so your message can reach me."
    ),
    "email.verify.button": "Confirm offer request",
    "email.verify.link_hint": "If the button does not work, copy this link into your browser:",
    "email.verify.expiry": "The link is valid for {hours} hours.",
    "email.verify.ignore": "If you did not send this request, simply ignore this e-mail.",
    "email.confirm.subject": "I received your offer request — Anita Tortái",
    "email.confirm.greeting": "Dear {name},",
    "email.confirm.body": (
        "Thank you, your offer request has arrived! I will contact you soon with "
        "the details and a price offer."
    ),
    "email.confirm.summary": "Request details",
    "email.chef.subject": "New offer request: {name} — {due_date}",
    "email.chef.title": "A new offer request has arrived",
    "email.field.name": "Name",
    "email.field.email": "E-mail",
    "email.field.phone": "Phone",
    "email.field.due_date": "Date of the event",
    "email.field.cake_type": "Cake type",
    "email.field.flavor": "Flavour",
    "email.field.portions": "Slices",
    "email.field.description": "Other requests",
    "email.field.locale": "Language",
    "email.footer": "Anita Tortái — baked with love · anitatortai.hu",
    "privacy.title": "Privacy notice",
}

DE: dict[str, str] = {
    "app.title": "Anita Tortái — Angebotsanfrage",
    "app.tagline": "mit Liebe gebacken",
    "app.language": "Sprache",
    "nav.home": "Startseite",
    "nav.cakes": "Torten",
    "nav.desserts": "Desserts",
    "nav.about": "Über mich",
    "nav.offer": "Angebotsanfrage",
    "nav.contact": "Kontakt",
    "nav.privacy": "Datenschutzerklärung",
    "footer.blurb": "Individuelle, handgefertigte Torten in Szentendre und Umgebung.",
    "footer.contact": "Kontakt",
    "footer.info": "Informationen",
    "footer.offer_hint": "Oder schreiben Sie mir einfach eine Nachricht!",
    "footer.rights": "Alle Rechte vorbehalten.",
    "hero.title": "Individuelle, handgefertigte Torten",
    "hero.location": "in Szentendre und Umgebung.",
    "hero.body": "Jede Torte ist eine Geschichte, die wir gemeinsam erschaffen.",
    "hero.cta": "Angebot anfragen",
    "hero.cta_gallery": "Torten ansehen",
    "why.title": "Warum ich?",
    "why.handmade.title": "Handgefertigte Dekorationen",
    "why.handmade.body": "Jedes Detail entsteht sorgfältig in Handarbeit.",
    "why.premium.title": "Premium-Zutaten",
    "why.premium.body": "Ich arbeite nur mit hochwertigen Zutaten.",
    "why.custom.title": "Individuelles Design",
    "why.custom.body": "Entsteht aus Ihrer ganz eigenen Idee.",
    "why.love.title": "Mit Liebe gebacken",
    "why.love.body": "In jede Torte lege ich mein Herzblut.",
    "steps.title": "Wie funktioniert es?",
    "steps.1.title": "Angebotsanfrage",
    "steps.1.body": "Füllen Sie das Formular aus und beschreiben Sie Ihre Ideen.",
    "steps.2.title": "Abstimmung",
    "steps.2.body": "Ich melde mich bei Ihnen und wir klären die Details.",
    "steps.3.title": "Herstellung",
    "steps.3.body": "Ich fertige Ihre einzigartige Torte mit Herz und Seele.",
    "steps.4.title": "Abholung",
    "steps.4.body": "Sie holen die Torte ab — die Feier kann beginnen!",
    "gallery.title": "Torten",
    "gallery.preview_title": "Einige meiner früheren Arbeiten",
    "gallery.all": "Alle Torten ansehen",
    "gallery.desserts_title": "Desserts",
    "gallery.placeholder_note": (
        "Fotos folgen in Kürze — fragen Sie in der Zwischenzeit gerne ein Angebot an!"
    ),
    "about.title": "Über mich",
    "about.body1": (
        "Hallo! Ich bin Anita, Gründerin der Tortenmanufaktur Anita Tortái. "
        "In Szentendre und Umgebung fertige ich individuelle, handdekorierte "
        "Torten für Geburtstage, Hochzeiten und jeden besonderen Anlass."
    ),
    "about.body2": (
        "Für mich ist jede Torte eine Geschichte: Ihre. Ich höre mir Ihre Idee an "
        "und erschaffe sie mit Herz und Seele aus Premium-Zutaten — mit Liebe gebacken."
    ),
    "about.cta": "Fragen Sie ein Angebot an!",
    "contact.title": "Kontakt",
    "contact.body": "Fragen, oder möchten Sie eine Idee besprechen? Schreiben Sie einfach!",
    "contact.email": "E-Mail",
    "contact.area": "Szentendre und Umgebung",
    "contact.area_label": "Abholung",
    "contact.area_note": "Abholung zu einem vorab vereinbarten Zeitpunkt.",
    "form.title": "Angebotsanfrage",
    "form.intro": "Füllen Sie das Formular aus, und ich melde mich in Kürze bei Ihnen!",
    "form.name": "Name",
    "form.name_ph": "Geben Sie Ihren Namen ein",
    "form.email": "E-Mail-Adresse",
    "form.email_ph": "Geben Sie Ihre E-Mail-Adresse ein",
    "form.email_hint": "An diese Adresse senden wir den Bestätigungslink.",
    "form.phone": "Telefonnummer",
    "form.phone_ph": "Geben Sie Ihre Telefonnummer ein",
    "form.optional": "optional",
    "form.due_date": "Datum des Anlasses",
    "form.due_date_hint": "Bitte fragen Sie Ihr Angebot mindestens {days} Tage im Voraus an.",
    "form.cake_type": "Tortentyp / Thema",
    "form.cake_type_ph": "Wählen Sie aus den Optionen",
    "form.cake_type.birthday": "Geburtstagstorte",
    "form.cake_type.kids": "Kindertorte",
    "form.cake_type.wedding": "Hochzeitstorte",
    "form.cake_type.shaped": "Motivtorte",
    "form.cake_type.dessert": "Desserts",
    "form.cake_type.other": "Sonstiges",
    "form.portions": "Anzahl der Stücke",
    "form.portions_ph": "z. B. 12 Stück",
    "form.flavor": "Geschmack",
    "form.flavor_hint": "falls Sie schon eine Idee haben",
    "form.flavor_ph": "Geschmack wählen",
    "form.flavor.csoki": "Schokolade",
    "form.flavor.vanilia": "Vanille",
    "form.flavor.gesztenye": "Kastanie",
    "form.flavor.tejszines_gyumolcsos": "Sahnig-fruchtig (Erdbeere, Heidelbeere, Himbeere usw.)",
    "form.flavor.karamella": "Karamell",
    "form.flavor.sos_karamell": "Gesalzenes Karamell",
    "form.flavor.turo": "Topfen (Túró)",
    "form.flavor.dio": "Walnuss",
    "form.flavor.fehercsoki": "Weiße Schokolade",
    "form.flavor.oroszkrem": "Russische Creme (Oroszkrém)",
    "form.flavor.citrom": "Zitrone",
    "form.flavor.pisztacia": "Pistazie",
    "form.flavor.egyeb": "Sonstiges",
    "form.description": "Weitere Wünsche / Anmerkungen",
    "form.description_ph": "Bitte beschreiben Sie Ihre Vorstellung…",
    "form.description_hint": (
        "Anlass, Geschmack, Dekoration, Beschriftung — jede Idee hilft! Höchstens {max} Zeichen."
    ),
    "form.consent": "Ich akzeptiere die {link}.",
    "form.consent_link": "Datenschutzerklärung",
    "form.submit": "Angebotsanfrage senden",
    "error.name_required": "Bitte geben Sie Ihren Namen ein.",
    "error.email_invalid": "Bitte geben Sie eine gültige E-Mail-Adresse ein.",
    "error.phone_invalid": "Bitte geben Sie eine gültige Telefonnummer ein.",
    "error.due_date_invalid": "Bitte wählen Sie ein Datum.",
    "error.due_date_too_soon": (
        "Das Datum ist zu knapp — mindestens {days} Tage Vorlauf sind nötig."
    ),
    "error.cake_type_required": "Bitte wählen Sie einen Tortentyp.",
    "error.portions_invalid": "Bitte geben Sie eine realistische Stückzahl ein.",
    "error.description_required": "Bitte beschreiben Sie Ihre Vorstellung.",
    "error.description_too_long": "Die Beschreibung ist zu lang (höchstens {max} Zeichen).",
    "error.consent_required": "Zur Anfrage müssen Sie die Datenschutzerklärung akzeptieren.",
    "error.too_fast": "Bitte senden Sie das Formular erneut ab.",
    "error.rate_limited": "Zu viele Versuche. Bitte versuchen Sie es später erneut.",
    "error.send_failed": "Der E-Mail-Versand ist fehlgeschlagen. Bitte versuchen Sie es später.",
    "submitted.title": "Fast geschafft!",
    "submitted.body": (
        "Wir haben eine Bestätigungs-E-Mail an {email} gesendet. Klicken Sie auf "
        "den Link darin, um Ihre Angebotsanfrage abzuschließen. Der Link ist "
        "{hours} Stunden gültig."
    ),
    "submitted.spam_hint": "Falls Sie die E-Mail nicht finden, prüfen Sie bitte den Spam-Ordner.",
    "verified.title": "Vielen Dank für Ihre Anfrage!",
    "verified.body": (
        "Ich habe Ihre Angebotsanfrage erhalten und melde mich bald mit den "
        "Details und einem Preisangebot."
    ),
    "verify.already.title": "Diese Anfrage ist bereits bestätigt",
    "verify.already.body": (
        "Sie haben diese Angebotsanfrage bereits bestätigt — nichts weiter zu tun."
    ),
    "verify.invalid.title": "Ungültiger oder abgelaufener Link",
    "verify.invalid.body": (
        "Dieser Bestätigungslink ist ungültig oder abgelaufen. Bitte senden Sie "
        "Ihre Anfrage erneut."
    ),
    "verify.back_home": "Zurück zur Startseite",
    "verify.failed.title": "Ihre Anfrage konnte nicht weitergeleitet werden",
    "verify.failed.body": (
        "Beim Weiterleiten Ihrer Angebotsanfrage ist ein vorübergehender Fehler "
        "aufgetreten. Ihr Bestätigungslink ist weiterhin gültig — bitte versuchen "
        "Sie es in ein paar Minuten erneut."
    ),
    "verify.failed.retry": "Erneut versuchen",
    "email.verify.subject": "Bestätigen Sie Ihre Angebotsanfrage — Anita Tortái",
    "email.verify.greeting": "Liebe(r) {name},",
    "email.verify.body": (
        "vielen Dank für Ihre Angebotsanfrage! Bitte bestätigen Sie Ihre "
        "E-Mail-Adresse über die Schaltfläche unten, damit Ihre Nachricht mich erreicht."
    ),
    "email.verify.button": "Angebotsanfrage bestätigen",
    "email.verify.link_hint": (
        "Falls die Schaltfläche nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:"
    ),
    "email.verify.expiry": "Der Link ist {hours} Stunden gültig.",
    "email.verify.ignore": (
        "Falls Sie diese Anfrage nicht gesendet haben, ignorieren Sie diese E-Mail bitte."
    ),
    "email.confirm.subject": "Ihre Angebotsanfrage ist eingegangen — Anita Tortái",
    "email.confirm.greeting": "Liebe(r) {name},",
    "email.confirm.body": (
        "vielen Dank, Ihre Angebotsanfrage ist eingegangen! Ich melde mich bald "
        "mit den Details und einem Preisangebot."
    ),
    "email.confirm.summary": "Details der Anfrage",
    "email.chef.subject": "Neue Angebotsanfrage: {name} — {due_date}",
    "email.chef.title": "Eine neue Angebotsanfrage ist eingegangen",
    "email.field.name": "Name",
    "email.field.email": "E-Mail",
    "email.field.phone": "Telefon",
    "email.field.due_date": "Datum des Anlasses",
    "email.field.cake_type": "Tortentyp",
    "email.field.flavor": "Geschmack",
    "email.field.portions": "Stücke",
    "email.field.description": "Weitere Wünsche",
    "email.field.locale": "Sprache",
    "email.footer": "Anita Tortái — mit Liebe gebacken · anitatortai.hu",
    "privacy.title": "Datenschutzerklärung",
}

CATALOGS: dict[str, dict[str, str]] = {"hu": HU, "en": EN, "de": DE}
SUPPORTED_LOCALES = tuple(CATALOGS)
LOCALE_NAMES = {"hu": "Magyar", "en": "English", "de": "Deutsch"}

# Cake-type option order for the form select (values stored in ORDERS.cake_type).
CAKE_TYPES = ("birthday", "kids", "wedding", "shaped", "dessert", "other")

# Available flavors (owner's list, 2026-07-18). Slugs stored in ORDERS.flavor;
# display names come from the catalogs (brand names stay untranslated).
FLAVORS = (
    "kinder",
    "kinder_maxi_king",
    "oreo",
    "raffaello",
    "csoki",
    "vanilia",
    "gesztenye",
    "tejszines_gyumolcsos",
    "karamella",
    "sos_karamell",
    "turo",
    "dio",
    "fehercsoki",
    "oroszkrem",
    "citrom",
    "pisztacia",
    "egyeb",
)


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
