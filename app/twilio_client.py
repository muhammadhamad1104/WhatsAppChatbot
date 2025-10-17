# app/twilio_client.py
import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # format: whatsapp:+14155238886

client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("✅ Twilio client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Twilio client: {e}")
else:
    logger.warning("⚠️ Twilio credentials not found in environment variables")

def send_whatsapp_message(to_number: str, body: str, max_retries: int = 3):
    """
    Send a WhatsApp message using Twilio with retry logic.
    
    Args:
        to_number: WhatsApp number in format 'whatsapp:+92300xxxxxxx'
        body: Message content (max 1600 characters for WhatsApp)
        max_retries: Number of retry attempts on failure
    
    Returns:
        Message SID on success, None on failure
    """
    if not client:
        error_msg = "Twilio client not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    if not to_number or not to_number.startswith("whatsapp:"):
        logger.error(f"Invalid to_number format: {to_number}")
        raise ValueError(f"to_number must be in format 'whatsapp:+...' but got: {to_number}")
    
    if not body or len(body.strip()) == 0:
        logger.warning("Empty message body, skipping send")
        return None
    
    # Truncate if too long (WhatsApp/Twilio limit is 1600 chars)
    if len(body) > 1600:
        body = body[:1597] + "..."
        logger.warning(f"Message truncated to 1600 characters")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 Sending WhatsApp message to {to_number} (attempt {attempt + 1}/{max_retries})")
            
            msg = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=body,
                to=to_number
            )
            
            logger.info(f"✅ Message sent successfully! SID: {msg.sid}")
            return msg.sid
            
        except Exception as e:
            logger.error(f"❌ Failed to send message (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt == max_retries - 1:
                # Last attempt failed
                logger.error(f"❌ All {max_retries} attempts failed for message to {to_number}")
                raise
            
            # Wait before retry
            import time
            time.sleep(1)
    
    return None


def validate_twilio_config() -> tuple[bool, str]:
    """
    Validate Twilio configuration.
    Returns (is_valid, message)
    """
    if not TWILIO_ACCOUNT_SID:
        return False, "TWILIO_ACCOUNT_SID not configured"
    
    if not TWILIO_AUTH_TOKEN:
        return False, "TWILIO_AUTH_TOKEN not configured"
    
    if not TWILIO_WHATSAPP_NUMBER:
        return False, "TWILIO_WHATSAPP_NUMBER not configured"
    
    if not client:
        return False, "Twilio client failed to initialize"
    
    return True, "Twilio configuration is valid"
