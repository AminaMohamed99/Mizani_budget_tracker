import os
import json
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types

# Initialize the Gemini client
client = genai.Client(api_key="")

DB_NAME = "ledger.db"

def init_db():
    """Creates the database file and the transactions table if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            item TEXT NOT NULL,
            total_amount INTEGER NOT NULL,
            raw_message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_transaction(parsed_data, raw_message):
    """Saves a successfully parsed transaction dictionary into the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO transactions (timestamp, transaction_type, item, total_amount, raw_message)
        VALUES (?, ?, ?, ?, ?)
    """, (
        current_time,
        parsed_data.get("transaction_type", "unknown"),
        parsed_data.get("item", "unknown"),
        parsed_data.get("total_amount", 0),
        raw_message
    ))
    
    conn.commit()
    conn.close()

def parse_and_log_merchant_message(user_message):
    """Parses the raw text using Gemini and automatically logs it to the database."""
    prompt = f"""
    You are an expert bookkeeping assistant for Kenyan micro-merchants. 
    Analyze the following message and extract the transaction details.
    
    User Message: "{user_message}"
    
    Your task is dual-purpose:
    1. Extract the raw transaction data.
    2. Write a short, encouraging confirmation message to the merchant.
    
    CRITICAL LANGUAGE RULE:
    - If the user writes to you in Swahili or Sheng, your `reply_message` MUST be written in natural, clear Swahili/Sheng.
    - If the user writes to you in English, your `reply_message` MUST be written in English.
    
    Respond ONLY with a raw JSON object containing these exact keys:
    - transaction_type: (either "sale", "expense", or "unknown")
    - item: (the item name, simplified)
    - total_amount: (the integer value in KES)
    - reply_message: (your short confirmation message in the matching language)
    
    Do not include any markdown formatting or extra text outside the JSON.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    try:
        data = json.loads(response.text.strip())
        
        # --- NEW: Only save to database if it's a valid sale or expense ---
        if data.get("transaction_type") in ["sale", "expense"]:
            save_transaction(data, user_message)
            
        return data
    except Exception as e:
        return {
            "transaction_type": "unknown", 
            "item": "error", 
            "total_amount": 0,
            "reply_message": "Samahani, sijapata hiyo vizuri. Jaribu tena."
        }
from flask import Flask, request
import urllib.parse

app = Flask(__name__)

import datetime

def get_today_earnings():
    """Calculates the total sales made today from ledger.db"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Get today's date formatted exactly how it's stored (e.g., YYYY-MM-DD)
        today_str = datetime.date.today().isoformat()
        
        # Query to sum up amounts where transaction_type is 'sale' and date matches today
        cursor.execute("""
            SELECT SUM(total_amount) 
            FROM transactions 
            WHERE transaction_type = 'sale' 
              AND timestamp LIKE ?
        """, (f"{today_str}%",))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result is not None else 0
    except Exception as e:
        print(f"Error calculating earnings: {e}")
        return 0
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    print("\n================ NEW INCOMING WEBHOOK COUGHT ================")
    
    # Check if data is coming through at all
    print(f"Raw Request Form Data: {dict(request.form)}") 
    
    # 1. Grab the actual message text sent by the user
    incoming_msg = request.form.get('Body', '').strip()
    print(f"Extracted Message Body: '{incoming_msg}'")
    
    if not incoming_msg:
        print("WARNING: Received an empty message body.")
        # Return blank TwiML so Twilio doesn't error out
        return "<?xml version='1.0' encoding='UTF-8'?><Response></Response>", 200

    try:
        # === CHANGE HAPPENS HERE ===
        msg_lower = incoming_msg.lower()
        
        # Check if the user is asking about daily balance/earnings
        if "how much" in msg_lower or "made today" in msg_lower or "mauzo" in msg_lower:
            print("User requested today's earnings. Querying database...")
            today_total = get_today_earnings() # Make sure you added this function above!
            ai_reply = f"Today you have made a total of KSh {today_total:,}. Keep up the great work!"
        else:
            # Otherwise, route the normal message to your Gemini brain to log it
            print("Sending message to Gemini brain...")
            result = parse_and_log_merchant_message(incoming_msg)
            ai_reply = result.get("reply_message", "Sawa, nimepokea.")
            
        print(f"System responded successfully. Reply text: '{ai_reply}'")
        # === END OF CHANGE ===

    except Exception as e:
        print(f"ERROR during Gemini parsing/logging: {str(e)}")
        ai_reply = "Samahani, kumetokea hitilafu ya mfumo. Tafadhali jaribu tena baada ya muda mfupi."
    
    # 3. Format the response back in the specific TwiML XML format Twilio expects
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Message>{ai_reply}</Message>
    </Response>"""
    
    print("Sending TwiML response back to Twilio...")
    print("============================================================\n")
    return twiml_response, 200