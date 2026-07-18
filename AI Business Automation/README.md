# ⚖️ Mizani Budget Tracker

Mizani AI is a sleek, minimalist personal finance assistant tailored for localized mobile money tracking. Instead of relying on cluttered interfaces or tedious manual data entry, Mizani provides a clean, step-by-step questionnaire flow and features an automated API gateway designed to ingest and parse transaction data natively.

---

## 🚀 Features

- **Minimalist Step-by-Step Onboarding:** A clean, multi-step profile builder that captures user financial goals, target saving metrics, and discovery info without distracting or clunky brand avatars.
- **Automated SMS Gateway Endpoints:** A FastAPI backend receiver built to capture and parse M-Pesa transaction texts automatically via regular expressions (RegEx).
- **Interactive Financial Metrics:** Streamlit-powered dashboard featuring dynamic category charts and interactive weekly spending visualizations.
- **AI Financial Coach Insights:** Deep integration with generative AI models to provide hyper-actionable, conversational coaching notes based on your budget metrics.

---

## 🛠️ Tech Stack

- **Frontend UI:** [Streamlit](https://streamlit.io/)
- **Backend API:** [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- **Database:** SQLite
- **AI Processing:** Google GenAI (Gemini)
- **Data Parsing:** PyPDF & Python `re` (Regular Expressions)

---

## 💻 How to Get Started

### 1. Clone the Repository
```bash
git clone [https://github.com/AminaMohamed99/Mizani_budget_tracker.git](https://github.com/AminaMohamed99/Mizani_budget_tracker.git)
cd Mizani_budget_tracker