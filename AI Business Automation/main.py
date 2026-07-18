from google import genai
from google.genai import types

client = genai.Client()

# 1. SIMULATED INPUT: This represents a messy email hitting the inbox
customer_email = """
Hey, my kitchen sink has been completely blocked up since this morning. 
Water is starting to overflow onto the floor tiles. Are you guys open today 
and how much do you charge just to come out and take a look? Need someone ASAP.
Thanks, Dave.
"""

# 2. BUSINESS CONTEXT: The specific facts the AI must follow
business_rules = """
Company Name: QuickFix Plumbers
Working Hours: Mon-Fri, 8 AM - 6 PM. (Closed on weekends).
Call-out Fee: £45 flat rate for diagnostics.
Emergency contact phone: 07123-456789.
"""

print("Processing incoming email through Gemini System Agent...")

# 3. EXECUTING THE PROCESSING CORE
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=f"Please handle this customer email: {customer_email}",
    config=types.GenerateContentConfig(
        # Giving the AI a strict role and feeding it the business guidelines
        system_instruction=f"You are an automated email triage assistant for a local plumbing business. Your goal is to draft a polite response for the business owner to review. Use the following facts to answer accurately: {business_rules}. Keep the tone helpful but concise.",
        temperature=0.3 # Low temperature makes the AI more focused and less likely to invent facts
    )
)

print("\n--- DRAFT EMAIL CREATED FOR OWNER TO REVIEW ---")
print(response.text)