import sqlite3
from google import genai

# Initialize the Gemini Client
try:
    ai_client = genai.Client()
except Exception:
    ai_client = None

def init_personal_db():
    """Creates a dedicated database and table for personal spending if it doesn't exist"""
    conn = sqlite3.connect("personal_expenses.db")
    cursor = conn.cursor()
    # Create a table tailored for personal finance tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT
        )
    """)
    
    # Check if it's empty. If yes, insert some mock personal transactions to test with today
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        print(" Personal database empty. Inserting mock personal M-Pesa tracking data...")
        mock_data = [
            ("QAP04N99TG", 1500.0, "Food & Dining", "Naivas Supermarket", "2026-07-13"),
            ("QAP05M11XX", 350.0,  "Transport",     "Super Metro Matatu", "2026-07-13"),
            ("QAP06T44ZZ", 4500.0, "Shopping",      "Mitumba Clothes",    "2026-07-14"),
            ("QAP07R22AA", 2500.0, "Food & Dining", "KFC Dinner",         "2026-07-15"),
            ("QAP08K77BB", 200.0,  "Transport",     "Bolt Boda",          "2026-07-16"),
            ("QAP09P55CC", 8000.0, "Rent & Bills",  "Token Electricity",  "2026-07-17"),
            ("QAP10O33DD", 1200.0, "Food & Dining", "Zucchini Groceries", "2026-07-18")
        ]
        cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", mock_data)
        conn.commit()
    conn.close()

def get_weekly_spending():
    """Fetches total personal spending grouped by category over the last 7 days"""
    conn = sqlite3.connect("personal_expenses.db")
    cursor = conn.cursor()
    
    query = """
        SELECT category, SUM(amount) 
        FROM transactions 
        GROUP BY category;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return {category: total for category, total in results}

def generate_ai_advice(spending_data):
    """Feeds the personal spending data into Gemini for tailored budget coaching"""
    savings_goal = 3000
    dining_limit = 2000
    
    total_spent = sum(spending_data.values())
    food_spent = spending_data.get("Food & Dining", 0)

    prompt = f"""
    You are a friendly, realistic personal finance coach in Kenya tracking mobile money.
    The user's weekly goals are to save {savings_goal} KSh and keep dining/food costs below {dining_limit} KSh.
    Here is their actual M-Pesa personal category breakdown from their database this week:
    {spending_data}
    Total combined spending: {total_spent} KSh.
    
    Provide exactly 3 sentences of hyper-actionable, encouraging advice in a friendly tone telling them how they did against their goals.
    """
    
    if ai_client:
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"AI connection error: {e}. Try keeping food costs low!"
    else:
        return "Fallback Advice: Your personal Food & Dining spending exceeded your 2,000 KSh limit this week. Try cooking more at home next week to hit your 3,000 KSh savings target!"

if __name__ == "__main__":
    # Ensure our clean personal database is initialized
    init_personal_db()
    
    print(" Pulling personal transaction aggregates...")
    weekly_data = get_weekly_spending()
    print(f" Personal Spending Summary: {weekly_data}")
    
    print("\n Consulting Gemini for your weekly financial coaching...")
    advice = generate_ai_advice(weekly_data)
    print(f"\n AI Advisor Update:\n{advice}")