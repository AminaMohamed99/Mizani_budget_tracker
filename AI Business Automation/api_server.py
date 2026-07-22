import os
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import re
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

# Load environment variables from local .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        # Connect to Neon PostgreSQL in production / local
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        raise ValueError("DATABASE_URL environment variable is not set!")

def init_expanded_database():
    """Sets up user onboarding tables and multi-day tracking tables in Postgres"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            savings_goal REAL,
            dining_limit REAL,
            usage_reason TEXT,
            discovery_source TEXT,
            joined_date TEXT
        )
    """)
    
    # 2. Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT,
            day_of_week TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    
    # Create default sandbox user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    if count == 0:
        cursor.execute("""
            INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, ('demo123', 'Guest User', 3000.0, 2000.0, 'Track personal spending', 'Friend recommendation', '2026-07-18'))
        
        mock_data = [
            ("TX001", "demo123", 1500.0, "Food & Dining", "Naivas Supermarket", "2026-07-13", "Monday"),
            ("TX002", "demo123", 350.0,  "Transport",     "Super Metro Matatu", "2026-07-13", "Monday"),
            ("TX003", "demo123", 4500.0, "Rent & Bills",  "Token Electricity",  "2026-07-14", "Tuesday"),
            ("TX004", "demo123", 1200.0, "Food & Dining", "Zucchini Groceries", "2026-07-15", "Wednesday"),
            ("TX005", "demo123", 4500.0, "Shopping",      "Mitumba Clothes",    "2026-07-16", "Thursday"),
            ("TX006", "demo123", 2500.0, "Food & Dining", "KFC Dinner",         "2026-07-17", "Friday"),
            ("TX007", "demo123", 200.0,  "Transport",     "Bolt Boda",          "2026-07-18", "Saturday"),
            ("TX008", "demo123", 3500.0, "Rent & Bills",  "Wi-Fi Monthly Bill", "2026-07-19", "Sunday")
        ]
        for row in mock_data:
            cursor.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", row)
        
        conn.commit()
    
    cursor.close()
    conn.close()

# Define Lifespan Event to initialize database on server startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_expanded_database()
    yield

app = FastAPI(title="M-Pesa Personal AI Tracker API", lifespan=lifespan)

# Enable CORS so your frontend UI can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class UserOnboarding(BaseModel):
    username: str
    savings_goal: float
    dining_limit: float
    usage_reason: str
    discovery_source: str

class IncomingSMS(BaseModel):
    user_id: str
    sms_body: str

# 1. ENDPOINT: Onboarding
@app.post("/api/users/onboarding")
def onboard_user(user_data: UserOnboarding):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    generated_id = str(uuid.uuid4())[:8]
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO users (user_id, username, savings_goal, dining_limit, usage_reason, discovery_source, joined_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (generated_id, user_data.username, user_data.savings_goal, 
          user_data.dining_limit, user_data.usage_reason, user_data.discovery_source, current_date))
    
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "user_id": generated_id, "message": "Onboarding saved!"}

# 2. ENDPOINT: Summary
@app.get("/api/spending/summary")
def get_spending_summary(user_id: str = "demo123"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT savings_goal, dining_limit FROM users WHERE user_id = %s", (user_id,))
    user_row = cursor.fetchone()
    savings_goal = user_row["savings_goal"] if user_row else 3000.0
    dining_limit = user_row["dining_limit"] if user_row else 2000.0
    
    cursor.execute("SELECT SUM(amount) AS total_spent, COUNT(*) AS tx_count FROM transactions WHERE user_id = %s", (user_id,))
    stats = cursor.fetchone()
    conn.close()
    
    return {
        "total_spending_this_week": stats["total_spent"] or 0 if stats else 0,
        "transaction_count": stats["tx_count"] or 0 if stats else 0,
        "weekly_savings_goal": savings_goal,
        "max_dining_budget": dining_limit
    }

# 3. ENDPOINT: Chart Data
@app.get("/api/charts/category-summary")
def get_chart_data(user_id: str = "demo123", day: str = "All"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if day == "All":
        cursor.execute("SELECT category, SUM(amount) AS total FROM transactions WHERE user_id = %s GROUP BY category", (user_id,))
    else:
        cursor.execute("SELECT category, SUM(amount) AS total FROM transactions WHERE user_id = %s AND day_of_week = %s GROUP BY category", (user_id, day.capitalize()))
        
    results = cursor.fetchall()
    conn.close()
    
    return {
        "labels": [row["category"] for row in results],
        "datasets": [row["total"] for row in results]
    }

# 4. ENDPOINT: AI Advice
@app.get("/api/ai/advice")
def get_ai_advice(user_id: str = "demo123"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, savings_goal, dining_limit FROM users WHERE user_id = %s", (user_id,))
    user_row = cursor.fetchone()
    username = user_row["username"] if user_row else "Guest"
    savings_goal = user_row["savings_goal"] if user_row else 3000
    dining_limit = user_row["dining_limit"] if user_row else 2000
    
    cursor.execute("SELECT category, SUM(amount) AS total FROM transactions WHERE user_id = %s GROUP BY category", (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    spending_data = {row["category"]: row["total"] for row in results}
    total_spent = sum(spending_data.values())
    
    prompt = f"""
    You are a friendly personal finance coach in Kenya tracking mobile money.
    Address the user as {username}. Their weekly target is to save {savings_goal} KSh and keep dining/food below {dining_limit} KSh.
    Current spending breakdown: {spending_data}
    Total spent: {total_spent} KSh.
    
    Provide exactly 3 sentences of hyper-actionable advice celebrating milestones or giving explicit coaching feedback based on their targets.
    """
    
    try:
        # Initialize client inside request handler to prevent lifecycle async errors
        client = genai.Client()
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return {"advice": response.text.strip()}
    except Exception as e:
        return {"advice": f"Habari {username}! Your food spending is currently being monitored. Let's make sure we hit that {savings_goal} KSh goal!"}

# 5. ENDPOINT: SMS Receiver
@app.post("/api/transactions/auto-sms")
def process_automated_sms(payload: IncomingSMS):
    text = payload.sms_body
    
    if "Confirmed." not in text or "Ksh" not in text:
        return {"status": "ignored", "message": "Not a valid transaction format statement message."}
        
    try:
        tx_id = text.split()[0]
        
        amount_match = re.search(r"Ksh([\d,]+\.\d\d)", text)
        amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0
        
        vendor = "Unknown Vendor"
        if "paid to " in text:
            vendor = text.split("paid to ")[1].split(" on")[0]
        elif "sent to " in text:
            vendor = text.split("sent to ")[1].split(" on")[0]
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")
        
        category = "Other"
        lowered_vendor = vendor.lower()
        if any(k in lowered_vendor for k in ["kfc", "naivas", "zucchini", "restaurant", "food", "cafeteria"]):
            category = "Food & Dining"
        elif any(k in lowered_vendor for k in ["super metro", "bolt", "uber", "matatu", "boda", "taxi"]):
            category = "Transport"
        elif any(k in lowered_vendor for k in ["token", "safaricom", "wifi", "bill", "airtime"]):
            category = "Rent & Bills"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (id, user_id, amount, category, description, date, day_of_week)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (tx_id, payload.user_id, amount, category, vendor, current_date, current_day))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success", 
            "extracted": {
                "tx_id": tx_id, 
                "amount": amount, 
                "vendor": vendor, 
                "category": category
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Processing metrics failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)