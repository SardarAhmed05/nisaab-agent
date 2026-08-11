# Nisaab — Your Personal Finance Agent

![Agentic AI](https://img.shields.io/badge/Architecture-Agentic_AI-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/Framework-LangGraph_StateGraph-000000?style=for-the-badge&logo=langchain)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI_Python_3.11+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Inference-Groq_Ultra--Fast_LPUs-f34f29?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

> **Take control of your finances with clarity.**  
> Nisaab is an autonomous, production-grade **Agentic AI Assistant** designed to manage income, track multi-category expenses across global currencies, enforce budget limits, analyze financial health, and guide wealth goals through natural language conversations.

---

## 🤖 Core Highlight: Agentic AI Architecture

At the heart of Nisaab is a stateful **Agentic AI Core** built on **LangGraph**. Unlike basic chatbots, Nisaab operates as an autonomous agent with reasoning capabilities, database tool binding, human-in-the-loop safety, and proactive goal assistance.

```
                  ┌───────────────────────────────┐
                  │      User Input Message       │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │    resolve_user Node (Auth)   │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │   agent Node (LangGraph LLM)  │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
         (Requires Tool Call)             (Direct Text Output)
                  │                               │
                  ▼                               ▼
       ┌─────────────────────┐                 ┌─────┐
       │   should_continue   │                 │ END │
       └──────────┬──────────┘                 └─────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   (Risky Action)     (Safe Action)
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ confirm Node  │   │  tools Node   │
│(Human-in-Loop)│   │  (Exec DB)    │
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
      (Loop Back to Agent Node)
```

### 🧠 Key Agentic Capabilities

- **Autonomous Tool Execution**: Automatically binds and executes 14+ financial database tools (`add_transaction`, `create_budget`, `get_balance`, `get_total_expenses`, `get_category_summary`, `set_user_currency`, etc.) based on natural conversation context.
- **🛡️ Human-in-the-Loop (HITL) Safety**: Sensitive operations (`delete_transaction`, `update_transaction`, `delete_budget`) trigger an explicit confirmation flow (`confirm_node`), ensuring user approval before database mutations occur.
- **🌍 Real-Time Multi-Currency Engine**: Log expenses in foreign currencies (*"$50 USD"*, *"100 SAR"*, *"30 EUR"*) or tell Nisaab to *"Set my preferred currency to USD"*. Converts amounts at real-time FX rates automatically.
- **💡 Proactive Budget Proposals**: When a user mentions a goal or trip with an amount (e.g. *"I'm planning a vacation for 100k"*), Nisaab generates a budget outline and proactively asks: *"Would you like me to set up a ₨100,000 budget for Vacation in your Nisaab account right now?"*.
- **🚫 Zero False Actions & Anti-Hallucination**: Enforces strict system prompt guardrails forbidding the agent from claiming a database change occurred unless the underlying tool executed successfully.
- **🌐 Universal Financial Domain Boundaries**: Full coverage of real-world financial goals (vacations, weddings, buying a car/laptop, starting a business, tuition, home renovation) while gracefully filtering out non-financial queries.

---

## ⚡ 4-Tier Free Multi-Provider LLM Fallback Chain

To maintain 99.9% availability with **$0.00 API costs**, Nisaab implements a multi-tier fallback mechanism across separate rate-limit quota buckets and providers:

```text
               ┌──────────────────────────────────────────────┐
               │ Tier 1: Groq Llama 3.3 70B (Primary 70B Model)│
               └──────────────────────┬───────────────────────┘
                                      │ (If Rate-Limited / 429)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ Tier 2: Groq Llama 3.1 8B (Separate 14.4k RPD)│
               └──────────────────────┬───────────────────────┘
                                      │ (If Rate-Limited / 429)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ Tier 3: Groq Mixtral 8x7B (Separate MoE Quota)│
               └──────────────────────┬───────────────────────┘
                                      │ (If Provider Outage)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ Tier 4: OpenRouter Dynamic Free Auto-Router  │
               │         (openrouter/free)                    │
               └──────────────────────────────────────────────┘
```

1. **Tier 1 (Primary)**: `llama-3.3-70b-versatile` *(Groq Free 70B Flagship)*
2. **Tier 2 (Fallback 1)**: `llama-3.1-8b-instant` *(Groq Free 8B — separate daily request quota)*
3. **Tier 3 (Fallback 2)**: `mixtral-8x7b-32768` *(Groq Free 8x7B MoE — separate quota bucket)*
4. **Tier 4 (Fallback 3)**: `openrouter/free` *(OpenRouter Dynamic Auto-Router — automatically selects active free models without hardcoded ID churn risk)*

---

## ✨ Additional Features

- **🌐 Top 6 Worldwide Currency Selector**: Interactive Balance Card selector supporting **PKR (₨)**, **USD ($)**, **EUR (€)**, **GBP (£)**, **SAR**, and **AED** with live real-time rate conversion.
- **🔐 Single Sign-On (SSO) & JWT Security**: Secure password hashing (`bcrypt`), JWT token verification, login rate-limiting, and native 1-click **Continue with Google** SSO.
- **📊 Real-Time Analytics Dashboard**: Visual category spending donut charts, net income vs. expense progress, and live transaction feeds.
- **🧹 Automated Clean Chat History**: Automatically purges empty/abandoned chat sessions, keeping the user's sidebar history pristine.
- **✉️ Responsive HTML Email Digests**: Scheduled daily background email summaries formatted with UTF-8 MIME multipart cards.

---

## 🏗️ Project Architecture

```text
nisaab-agent/
├── alembic/                  # Database migration scripts & history
├── app/
│   ├── agent/                # 🤖 Agentic AI Engine (LangGraph Core)
│   │   ├── graph.py          # StateGraph workflow, routing & MODEL_CHAIN
│   │   ├── models.py         # Multi-provider LLM tier configurations
│   │   ├── prompts.py        # System prompt, domain guardrails & rules
│   │   ├── state.py          # AgentState definitions
│   │   └── tools.py          # 14+ Financial database & FX tools
│   ├── api/                  # FastAPI REST API Controllers
│   │   ├── analytics.py      # Category breakdown & summary analytics
│   │   ├── auth.py           # JWT & Google SSO authentication
│   │   ├── balance.py        # Real-time balance calculations
│   │   ├── chat.py           # Chat streaming & response sanitization
│   │   ├── transactions.py   # Transaction CRUD endpoints
│   │   └── user.py           # User profile & currency settings
│   ├── auth/                 # JWT token management & security middleware
│   ├── db/                   # SQLAlchemy models, sessions, and CRUD operations
│   ├── notifications/        # UTF-8 MIME multipart email template sender
│   ├── scheduler/            # APScheduler background tasks
│   ├── schemas/              # Pydantic data validation models
│   ├── static/               # CSS3 design system, icons, & JS app logic
│   ├── templates/            # Jinja2 HTML5 UI templates
│   └── main.py               # FastAPI entry point & app router mounting
├── tests/                    # Unit and integration test suite
├── .env.example              # Environment variable template
├── alembic.ini               # Database migration configuration
├── LICENSE                   # Official MIT License file
├── Procfile                  # Production deployment configuration
└── requirements.txt          # Python package dependencies
```

---

## 🚀 Quick Start Guide

### 1. Clone & Environment Setup
```bash
git clone https://github.com/your-username/nisaab-agent.git
cd nisaab-agent

# Create & activate virtual environment
python -m venv venv
# Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 3. Run Database Migrations & Start Server
```bash
alembic upgrade head
uvicorn app.main:app --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 📄 License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
