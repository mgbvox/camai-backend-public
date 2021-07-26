from app.core.config import settings
async def get_validation_check():
    return settings.KEY_HASH
