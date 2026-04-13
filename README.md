# TerraDesk AI — IT Support Intelligence Platform

AI-powered IT support triage and resolution system built with a LangGraph multi-agent pipeline. Classifies incoming tickets, searches a knowledge base for proven resolutions, generates step-by-step fix instructions, drafts professional responses, and routes to the right team member — all automatically.

**Portfolio:** [rajaabdullah.com](https://rajaabdullah.com)

---

## Architecture

    Streamlit UI (5 pages)
        ├── 📊 Dashboard — real-time ticket analytics (Plotly)
        ├── 🎯 New Ticket — AI-powered classification & resolution
        ├── 📋 All Tickets — filter, manage, update status
        ├── 📚 Knowledge Base — searchable resolved issues
        └── 🔌 Freshdesk Sync — external ticketing integration
             │
             ▼
    LangGraph Pipeline (3 agents)
        ├── Agent 1: Classifier → category, priority, routing, SSO/MFA detection
        ├── Agent 2: KB Search → matches against resolved issue patterns
        └── Agent 3: Responder → resolution steps, response draft, internal notes
             │
             ▼
    Data Layer
        ├── SQLite — tickets, knowledge base, activity log
        └── Freshdesk REST API — pull/push tickets from external system

## Tech Stack

- **Python** — primary language
- **LangGraph** — multi-agent orchestration pipeline
- **Anthropic Claude API** — LLM for classification, reasoning, and response generation
- **Streamlit** — frontend dashboard and UI
- **SQLite** — ticket database, knowledge base, audit trail
- **Plotly** — interactive analytics charts
- **Freshdesk API** — integration with external ticketing system
- **Requests** — HTTP client for API integration

## Key Features

- **AI Ticket Classification** — automatically categorises tickets (M365, Salesforce, Intune, SharePoint, Security, Network, Onboarding/Offboarding), assigns priority, routes to the right engineer
- **Knowledge Base Search** — Agent 2 searches past resolutions before generating new ones, getting smarter over time
- **Resolution Generation** — step-by-step fix instructions tailored to the specific environment
- **Response Drafting** — professional reply ready to send to the person who raised the ticket
- **SSO/MFA Detection** — flags identity-related issues that may need Conditional Access review
- **Freshdesk Integration** — connects to a real ticketing platform via REST API
- **Analytics Dashboard** — ticket volume by category, priority distribution, team workload, recent activity
- **Audit Trail** — every action logged for accountability

## Setup

    # Clone the repo
    git clone https://github.com/RajaAbdullah4002/terradesk-ai.git
    cd terradesk-ai

    # Create virtual environment
    python -m venv venv
    venv\Scripts\activate          # Windows
    source venv/bin/activate       # Mac/Linux

    # Install dependencies
    pip install -r requirements.txt

    # Add your API key
    mkdir .streamlit
    echo 'ANTHROPIC_API_KEY = "your-key-here"' > .streamlit/secrets.toml

    # Seed the database with demo data
    python seed_data.py

    # Run the app
    python -m streamlit run app.py

## Pipeline Flow

1. **User submits a ticket** via the Streamlit UI or Freshdesk sync
2. **Agent 1 (Classifier)** analyses the text and returns: category, priority, assigned engineer, affected systems, SSO/MFA flag, estimated resolution time
3. **Agent 2 (KB Search)** queries the SQLite knowledge base for matching past resolutions using keyword matching
4. **Agent 3 (Responder)** takes the classification + KB matches and generates: resolution steps, a professional response draft, and internal notes
5. **Ticket is saved** to SQLite with full audit trail
6. **Dashboard updates** in real-time with new analytics

## Project Structure

    terradesk-ai/
    ├── app.py                  # Streamlit app — 5-page UI
    ├── pipeline.py             # LangGraph 3-agent pipeline
    ├── database.py             # SQLite data layer (tickets, KB, activity log)
    ├── freshdesk_client.py     # Freshdesk REST API client
    ├── seed_data.py            # Demo data — 10 KB articles, 8 sample tickets
    ├── requirements.txt        # Python dependencies
    ├── .streamlit/
    │   └── config.toml         # Streamlit theme config
    └── README.md

## Author

**Roger (Raja Abdullah)**
- Portfolio: [rajaabdullah.com](https://rajaabdullah.com)
- GitHub: [github.com/RajaAbdullah4002](https://github.com/RajaAbdullah4002)
- LinkedIn: [linkedin.com/in/mabdullah010](https://linkedin.com/in/mabdullah010)