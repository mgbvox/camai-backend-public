from app.core.config import settings
from signalwire.rest import Client as signalwire_client
from app.utils.db import should_alert
from datetime import datetime

SW_CLIENT = signalwire_client(settings.SIGNALWIRE_PROJECT_ID,
                              settings.SIGNALWIRE_ACCESS_TOKEN,
                              signalwire_space_url=settings.SIGNALWIRE_DOMAIN)


async def alert_sms(body: str, traceback:str = None) -> bool:
    do_alert = await should_alert(patient_db=settings.MONGO_DATABASE)
    if do_alert:
        for phone_number in settings.NOTIFICATION_PHONE_NUMBERS:

            full_body = f'''MESSAGE:
{body}
---------------------
DETAILS:
DB: {settings.MONGO_DATABASE}
TIME: {datetime.now().isoformat()}'''
            if traceback:
                full_body += f'---------------------\n{traceback}'

            message = SW_CLIENT.messages.create(
                from_=settings.SIGNALWIRE_PHONE_NUMBER,
                body=full_body,
                to=str(phone_number)
            )

            if not message.error_code:
                return True
            return False
    else:
        print('NOT ALERTING!')
        return True
