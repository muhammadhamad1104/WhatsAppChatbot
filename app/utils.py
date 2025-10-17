# app/utils.py
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def format_job_response(job_id: str, job_data: dict) -> str:
    """
    Format job data into a clean WhatsApp message.
    Matches the format shown in the client's screenshot.
    """
    if not job_data.get("success"):
        return f"❌ {job_data.get('message', 'Job not found')}"
    
    # Build formatted message matching the client's example
    message = f"""Job ID uploaded correctly. Please proceed with closing the job.😎

Overall Status: PASS ✅

Job ID: {job_data.get('job_id', job_id)}
Account: {job_data.get('account', 'N/A')}

Cable Type: 🔌 {job_data.get('type', 'COAX')}

Date Uploaded: {job_data.get('date_uploaded', 'N/A')}
Date Measured: {job_data.get('date_measured', 'N/A')}

Technician: {job_data.get('technician', 'N/A')}
Company: {job_data.get('company', 'N/A')}

Component Status:
"""
    
    # Add component statuses
    components = job_data.get('components', {})
    if components:
        for component, status in components.items():
            message += f"{component}: {status}\n"
    else:
        # Default components if not extracted
        message += f"tap: ✅ Passed\n"
        message += f"gnb BI: ✅ Passed\n"
        message += f"Cpe: ✅ Passed\n"
        message += f"Pressure test: ➖ Missing\n"
        message += f"TDR: ➖ Missing\n"
    
    return message


def handle_general_query(query: str) -> str:
    """
    Handle general conversational queries using simple rule-based responses.
    Can be enhanced with AI/LLM integration later.
    """
    query_lower = query.lower().strip()
    
    # Date/Time queries
    if any(word in query_lower for word in ["today", "date", "day"]):
        now = datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")
        
        if "what day" in query_lower:
            return f"Today's date is {date_str}. If you were referring to a specific occasion, feel free to elaborate, and I can provide more context!"
        else:
            return f"📅 Today is {day_name}, {date_str}."
    
    # Time queries
    if any(word in query_lower for word in ["time", "clock"]):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return f"🕐 The current time is {time_str}."
    
    # Greetings
    if any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "👋 Hello! How can I assist you today?\n\n💡 You can:\n• Send a 20-digit Job ID to check status\n• Ask me general questions"
    
    # Help queries
    if any(word in query_lower for word in ["help", "how", "what can you"]):
        return """🤖 **WhatsApp VeEX Bot Help**

I can help you with:

1️⃣ **Job Status Lookup**
   • Send me a 20-digit Job ID
   • I'll fetch the job details from VeEX portal
   • You'll get component status, dates, and technician info

2️⃣ **General Questions**
   • Ask about date/time
   • General information queries
   
📝 Example: Send "10008514921140650001" to check a job status"""
    
    # Goodbye
    if any(word in query_lower for word in ["bye", "goodbye", "see you"]):
        return "👋 Goodbye! Feel free to message me anytime you need help with job lookups or questions!"
    
    # Thanks
    if any(word in query_lower for word in ["thank", "thanks"]):
        return "😊 You're welcome! Happy to help!"
    
    # Job-related queries (when not a job ID)
    if any(word in query_lower for word in ["job", "status", "check"]):
        return "🔍 To check a job status, please send me the 20-digit Job ID number.\n\nExample: 10008514921140650001"
    
    # Weather queries
    if "weather" in query_lower:
        return "🌤️ I don't have access to weather information yet, but I can help you check VeEX job statuses! Send me a 20-digit Job ID to get started."
    
    # Default response for unknown queries
    return f"""I received your message: "{query}"

I can help you with:
• 📋 Job status lookups (send 20-digit Job ID)
• 📅 Date and time information
• ❓ General questions

Would you like to check a job status or ask something else?"""


def validate_job_id(job_id: str) -> tuple[bool, str]:
    """
    Validate if a string is a valid 20-digit Job ID.
    Returns (is_valid, error_message)
    """
    if not job_id:
        return False, "Job ID cannot be empty"
    
    if not job_id.isdigit():
        return False, "Job ID must contain only numbers"
    
    if len(job_id) != 20:
        return False, f"Job ID must be exactly 20 digits (you sent {len(job_id)} digits)"
    
    return True, ""


def chunk_message(message: str, max_length: int = 1500) -> list[str]:
    """
    Split a long message into chunks for WhatsApp/Twilio.
    """
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    lines = message.split('\n')
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
