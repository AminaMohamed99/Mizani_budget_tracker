import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Set up page styling
st.set_page_config(page_title="Mzani AI Tracker", page_icon="⚖️", layout="centered")

# Custom CSS injection for a clean, minimalist layout
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Fredoka', sans-serif !important;
    }
    
    .duo-card {
        background-color: #FFFFFF;
        border: 2px solid #E5E5E5;
        border-bottom: 5px solid #E5E5E5;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .streak-banner {
        background-color: #FF9600;
        color: white;
        border-radius: 16px;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        border-bottom: 5px solid #E67E00;
        margin-bottom: 20px;
    }
    
    .speech-bubble {
        background-color: #1CB0F6;
        color: white;
        border-radius: 16px;
        padding: 20px;
        border-bottom: 5px solid #1480B3;
        font-size: 16px;
        margin-top: 10px;
        position: relative;
    }
    </style>
""", unsafe_allow_html=True)

API_BASE = "http://127.0.0.1:8000"

# Track current user state using Streamlit session memory
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "demo123" # Default sandbox profile
if "is_onboarding" not in st.session_state:
    st.session_state["is_onboarding"] = False

# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.markdown("### ⚙️ User Profiles")
    if st.button("✨ Create New Account (Onboarding)"):
        st.session_state["is_onboarding"] = True
        st.session_state["ob_step"] = 1
        st.session_state["answers"] = {}
        st.rerun()
    if st.button("🔄 Switch to Demo Sandbox"):
        st.session_state["user_id"] = "demo123"
        st.session_state["is_onboarding"] = False
        st.rerun()
    st.caption(f"Current User ID: {st.session_state['user_id']}")

# --- ONBOARDING FLOW SCREEN (CLEAN STEP-BY-STEP WIZARD) ---
if st.session_state["is_onboarding"]:
    if "ob_step" not in st.session_state:
        st.session_state["ob_step"] = 1
        st.session_state["answers"] = {}

    current_step = st.session_state["ob_step"]
    total_steps = 5
    progress_percentage = int((current_step / total_steps) * 100)

    # Sleek top progress bar
    st.markdown(f"""
        <div style="width: 100%; background-color: #E5E5E5; border-radius: 10px; height: 8px; margin-bottom: 40px;">
            <div style="width: {progress_percentage}%; background-color: #1CB0F6; height: 8px; border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    """, unsafe_allow_html=True)

    _, col_main, _ = st.columns([1, 6, 1])
    
    with col_main:
        # STEP 1: Name Input
        if current_step == 1:
            st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>Welcome to Mzani AI. What should we call you?</h2>", unsafe_allow_html=True)
            name_input = st.text_input("", placeholder="Enter your name...", key="ob_name", label_visibility="collapsed")
            st.write("")
            if st.button("Continue", use_container_width=True):
                if name_input.strip():
                    st.session_state["answers"]["username"] = name_input.strip()
                    st.session_state["ob_step"] = 2
                    st.rerun()
                else:
                    st.error("Please enter your name before continuing!")

        # STEP 2: Discovery Source
        elif current_step == 2:
            st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>How did you discover Mzani AI?</h2>", unsafe_allow_html=True)
            source_options = ["TikTok / Social Media", "Friend or Family", "Google Search", "Community Group"]
            for opt in source_options:
                if st.button(opt, use_container_width=True, key=f"src_{opt}"):
                    st.session_state["answers"]["discovery_source"] = opt
                    st.session_state["ob_step"] = 3
                    st.rerun()

        # STEP 3: Core Motivation
        elif current_step == 3:
            st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>What is your primary goal for using the app?</h2>", unsafe_allow_html=True)
            reasons = ["Save for an emergency fund", "Stop overspending on entertainment/dining", "Track business cashflow metrics", "Build general investing discipline"]
            for reason in reasons:
                if st.button(reason, use_container_width=True, key=f"res_{reason}"):
                    st.session_state["answers"]["usage_reason"] = reason
                    st.session_state["ob_step"] = 4
                    st.rerun()

        # STEP 4: Financial Goals
        elif current_step == 4:
            st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Set your weekly savings target</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #777; margin-bottom: 25px;'>This helps Mzani calculate your daily spending limits.</p>", unsafe_allow_html=True)
            goal = st.slider("Select Target Amount (KSh):", min_value=1000, max_value=20000, value=3000, step=500)
            st.write("")
            if st.button("Commit to Goal", use_container_width=True):
                st.session_state["answers"]["savings_goal"] = float(goal)
                st.session_state["answers"]["dining_limit"] = float(goal * 0.4)
                st.session_state["ob_step"] = 5
                st.rerun()

        # STEP 5: Final Confirmation
        elif current_step == 5:
            st.markdown("<h2 style='text-align: center; margin-bottom: 15px;'>Your profile is ready!</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #777; margin-bottom: 25px;'>Review your setup before generating your dashboard:</p>", unsafe_allow_html=True)
            st.json(st.session_state["answers"])
            st.write("")
            if st.button("Go to Dashboard", use_container_width=True):
                try:
                    res = requests.post(f"{API_BASE}/api/users/onboarding", json=st.session_state["answers"]).json()
                    st.session_state["user_id"] = res["user_id"]
                    st.session_state["is_onboarding"] = False
                    del st.session_state["ob_step"]
                    del st.session_state["answers"]
                    st.rerun()
                except Exception:
                    st.error("Error communicating with backend storage servers.")

# --- DASHBOARD FLOW SCREEN ---
else:
    st.markdown("## ⚖️ Mzani AI Coach")
    st.markdown('<div class="streak-banner">🔥 5 Day Budgeting Streak! Keep it up!</div>', unsafe_allow_html=True)

    try:
        current_uid = st.session_state["user_id"]
        
        # 1. Interactive Day Selection Tabs
        st.markdown("### 📅 Select Filtering View")
        day_view = st.selectbox("Choose Day Filter:", ["All Weeks Combined", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        api_day_param = "All" if day_view == "All Weeks Combined" else day_view
        
        # Fetch matching data from endpoints
        summary_res = requests.get(f"{API_BASE}/api/spending/summary?user_id={current_uid}").json()
        chart_res = requests.get(f"{API_BASE}/api/charts/category-summary?user_id={current_uid}&day={api_day_param}").json()
        advice_res = requests.get(f"{API_BASE}/api/ai/advice?user_id={current_uid}").json()
        
        # 2. Metric Block Displays
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="duo-card">
                    <span style="color: #777777; font-size: 14px; font-weight: bold;">TOTAL SPENT</span><br>
                    <span style="font-size: 28px; font-weight: 700; color: #1CB0F6;">{summary_res['total_spending_this_week']:,} KSh</span>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="duo-card">
                    <span style="color: #777777; font-size: 14px; font-weight: bold;">WEEKLY GOAL</span><br>
                    <span style="font-size: 28px; font-weight: 700; color: #2B70C9;">{summary_res['weekly_savings_goal']:,} KSh</span>
                </div>
            """, unsafe_allow_html=True)

        # 3. Dynamic Interactive Charts
        st.markdown('<div class="duo-card">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-top:0;'>📊 Spending Breakdown ({day_view.lower()})</h3>", unsafe_allow_html=True)
        
        if chart_res["labels"]:
            df = pd.DataFrame({
                "Category": chart_res["labels"],
                "Amount (KSh)": chart_res["datasets"]
            })
            fig = px.bar(
                df, x="Category", y="Amount (KSh)", 
                color="Category",
                color_discrete_sequence=["#1CB0F6", "#FF4B4B", "#FFC800", "#CE82FF"]
            )
            fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recorded transactions found matching this specific filtering day block.")
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. M-Pesa PDF Import Block
        st.markdown('<div class="duo-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>📥 Import Real M-Pesa Data</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drop your M-Pesa PDF e-Statement here to populate your live metrics:", type=["pdf"])
        
        if uploaded_file is not None:
            try:
                from pypdf import PdfReader
                reader = PdfReader(uploaded_file)
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text()
                
                st.success("PDF parsed successfully!")
                st.caption("Extracted Statement Preview:")
                st.text(full_text[:300] + "...")
            except Exception as pdf_err:
                st.error(f"Could not parse PDF file: {pdf_err}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 5. AI Coach Update Container
        st.write("### 🤖 Mzani Coach Update")
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 50px;">🤖</span>
                <div class="speech-bubble">
                    {advice_res['advice']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Connection error. Ensure api_server.py is running! Details: {str(e)}")