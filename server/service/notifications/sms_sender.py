import logging

logger = logging.getLogger(__name__)

def send_sms(phone: str, message: str) -> bool:
    logger.info(f"[SMS placeholder] Would send to {phone}: {message}")
    return True
