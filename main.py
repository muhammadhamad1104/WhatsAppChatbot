# main.py
import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.twilio_client import send_whatsapp_message
from app.scraper import get_job_info
from app.utils import format_job_response, handle_general_query
from datetime import datetime

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp_veex_bot")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "verify_token_default")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Twilio webhook endpoint for incoming WhatsApp messages.
    Handles both Job ID lookups and general conversational queries.
    """
    if request.method == "GET":
        return jsonify({"status": "webhook_online", "service": "WhatsApp VeEX Bot"}), 200

    # Twilio sends application/x-www-form-urlencoded by default
    from_number = request.form.get("From")  # e.g., 'whatsapp:+92300...'
    body = request.form.get("Body", "").strip()
    logger.info("📩 Incoming message from %s: %s", from_number, body)

    if not body:
        reply = "👋 Hi! I can help you with:\n\n1️⃣ Job lookups - Send me a 20-digit Job ID\n2️⃣ General questions - Ask me anything!\n\nWhat would you like to know?"
        send_whatsapp_message(from_number, reply)
        return jsonify({"status": "no_body"}), 200

    # Check if the message is a 20-digit Job ID
    first_word = body.strip().split()[0]
    
    if first_word.isdigit() and len(first_word) == 20:
        # Handle Job ID lookup
        job_id = first_word
        logger.info("🔍 Job ID detected: %s", job_id)
        
        # Send interim response
        send_whatsapp_message(from_number, f"🔍 Searching for Job ID: {job_id}\n⏳ Please wait...")

        try:
            job_data = get_job_info(job_id)
            
            if job_data and job_data.get("success"):
                msg = format_job_response(job_id, job_data)
            else:
                msg = f"❌ Job ID {job_id} not found or no data available.\n\nPlease check the Job ID and try again."
                
        except Exception as exc:
            logger.exception("❌ Error fetching job info")
            msg = f"⚠️ Error fetching job data:\n{str(exc)}\n\nPlease try again later."

        # Send response (with chunking if needed)
        send_whatsapp_message(from_number, msg)
        return jsonify({"status": "job_lookup_complete"}), 200
    
    else:
        # Handle general conversational query
        logger.info("💬 General query detected: %s", body)
        
        try:
            response = handle_general_query(body)
            send_whatsapp_message(from_number, response)
            return jsonify({"status": "general_query_complete"}), 200
            
        except Exception as exc:
            logger.exception("❌ Error handling general query")
            msg = "⚠️ Sorry, I encountered an error processing your question. Please try again."
            send_whatsapp_message(from_number, msg)
            return jsonify({"status": "error"}), 200

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    # Railway uses PORT, local uses FLASK_PORT
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 8000)))
    logger.info(f"🚀 Starting WhatsApp VeEX Bot on {host}:{port}")
    app.run(host=host, port=port, debug=False)
