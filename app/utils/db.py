from app.database.crypto import hash_string
from app.database.patient import query_db
from app.core.config import settings

async def _get_client():
    from app.main import MONGO_CLIENT
    return MONGO_CLIENT

async def check_email_address(email: str) -> str:
    this_email_hash = hash_string(email)
    existing_email_matches = await query_db({'base_email_hash': this_email_hash})
    n_matching = len(existing_email_matches) if existing_email_matches else 0
    extension = f'+{n_matching}' if n_matching > 0 else ''
    name, domain = email.split('@')
    incremented_email = f'{name}{extension}@{domain}'
    return incremented_email


async def should_alert(patient_db: str) -> bool:
    client = await _get_client()
    settings_doc = await client.settings.alerts.find_one({})
    alert_setting = settings_doc.get(f'send_alerts_{patient_db.lower()}')
    alert_bool = bool(alert_setting)
    return alert_bool
