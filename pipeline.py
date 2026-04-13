"""TerraDesk AI — LangGraph multi-agent pipeline for IT support ticket processing."""

import json
import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from anthropic import Anthropic

# ── State schema — this is what flows between agents ─────────

class TicketState(TypedDict):
    """State that passes through the entire pipeline."""
    # Input
    raw_text: str
    requester: str

    # Agent 1 output — Classifier
    category: Optional[str]
    priority: Optional[str]
    assigned_to: Optional[str]
    subject: Optional[str]
    related_systems: Optional[list]
    sso_mfa_related: Optional[bool]
    estimated_time: Optional[str]

    # Agent 2 output — KB Search
    kb_matches: Optional[list]
    kb_resolution_found: Optional[bool]

    # Agent 3 output — Responder
    resolution_steps: Optional[list]
    response_draft: Optional[str]
    resolution_notes: Optional[str]


# ── Claude API helper ────────────────────────────────────────

try:
    import streamlit as st
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
except:
    api_key = os.getenv("ANTHROPIC_API_KEY")

client = Anthropic(api_key=api_key)


def call_claude(system_prompt: str, user_message: str) -> str:
    """Call Claude API and return the text response."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text


# ── Agent 1: Classifier ─────────────────────────────────────

CLASSIFIER_PROMPT = """You are an IT support ticket classifier for Terra Firma Business Consulting.

Terra Firma is a Melbourne-based business and technology consulting firm with 200+ staff.
Their IT environment includes:
- Microsoft 365 (Outlook, Teams, Word, Excel, PowerPoint)
- Microsoft Entra ID (SSO, MFA, Conditional Access)
- Microsoft Intune (device management, compliance policies)
- Salesforce Sales Cloud (CRM, rate cards, user management)
- SharePoint Online and OneDrive (file storage, collaboration)
- Microsoft Defender (endpoint security, threat alerts)
- Standard office networking and hardware

IT Team:
- Blair Douglass (Systems Engineer): handles M365, Intune, Azure, Entra ID, SharePoint, security, networking, hardware
- Carolyn Hayward (IT Digital Lead): handles Salesforce administration, customisation, user management

Classify the ticket and respond ONLY with valid JSON, no markdown, no backticks:
{
    "category": one of ["Microsoft 365", "Salesforce", "Intune / Device", "SharePoint / Files", "Security / Access", "Network / Hardware", "Onboarding / Offboarding"],
    "priority": one of ["Low", "Medium", "High", "Critical"],
    "assigned_to": "Blair Douglass" or "Carolyn Hayward",
    "subject": "short summary of the issue in under 10 words",
    "related_systems": ["list", "of", "affected", "systems"],
    "sso_mfa_related": true or false,
    "estimated_time": "estimated resolution time like 15 mins or 1 hour"
}

Priority guide:
- Critical: total system outage, security breach, all users affected
- High: single user locked out, device lost/stolen, phishing confirmed
- Medium: feature not working, access request, minor issue
- Low: question, documentation request, future planning"""


def classifier_agent(state: TicketState) -> dict:
    """Agent 1: Classifies the ticket into category, priority, and assignee."""
    raw = state["raw_text"]

    response = call_claude(CLASSIFIER_PROMPT, f"Support ticket: \"{raw}\"")

    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback if Claude doesn't return valid JSON
        data = {
            "category": "Microsoft 365",
            "priority": "Medium",
            "assigned_to": "Blair Douglass",
            "subject": raw[:50],
            "related_systems": [],
            "sso_mfa_related": False,
            "estimated_time": "30 mins"
        }

    return {
        "category": data.get("category", "Microsoft 365"),
        "priority": data.get("priority", "Medium"),
        "assigned_to": data.get("assigned_to", "Blair Douglass"),
        "subject": data.get("subject", raw[:50]),
        "related_systems": data.get("related_systems", []),
        "sso_mfa_related": data.get("sso_mfa_related", False),
        "estimated_time": data.get("estimated_time", "30 mins"),
    }


# ── Agent 2: KB Search ───────────────────────────────────────

def kb_search_agent(state: TicketState) -> dict:
    """Agent 2: Searches knowledge base for matching past resolutions."""
    from database import search_kb

    raw = state["raw_text"]
    category = state.get("category")

    # Search by raw text keywords
    matches = search_kb(raw, category=category, limit=3)

    # If no category-specific matches, try without category filter
    if not matches:
        # Extract key words for broader search
        words = raw.lower().split()
        search_terms = ["mfa", "sso", "password", "login", "teams", "outlook",
                        "salesforce", "sharepoint", "intune", "vpn", "wifi",
                        "printer", "laptop", "phone", "authenticator", "licence",
                        "onboarding", "offboarding", "defender", "phishing"]

        for term in search_terms:
            if term in words:
                matches = search_kb(term, limit=3)
                if matches:
                    break

    return {
        "kb_matches": matches if matches else [],
        "kb_resolution_found": len(matches) > 0,
    }


# ── Agent 3: Responder ───────────────────────────────────────

RESPONDER_PROMPT = """You are an IT support resolution specialist for Terra Firma Business Consulting.

Given a classified support ticket and any matching knowledge base articles, generate:
1. Step-by-step resolution instructions (clear enough for a junior IT person to follow)
2. A professional response draft to send to the user who raised the ticket
3. Brief internal notes for the IT team

Respond ONLY with valid JSON, no markdown, no backticks:
{
    "resolution_steps": ["step 1", "step 2", "step 3", "step 4"],
    "response_draft": "Professional email/message to send to the user who raised the ticket",
    "resolution_notes": "Internal notes for the IT team — anything to watch out for"
}

Keep resolution steps practical and specific to Terra Firma's Microsoft + Salesforce environment.
If KB matches are provided, incorporate their proven resolutions.
Keep the response draft friendly but professional — Terra Firma values collegiality."""


def responder_agent(state: TicketState) -> dict:
    """Agent 3: Generates resolution steps, response draft, and internal notes."""
    context = f"""Ticket: "{state['raw_text']}"
Category: {state.get('category', 'Unknown')}
Priority: {state.get('priority', 'Medium')}
Assigned to: {state.get('assigned_to', 'Unassigned')}
SSO/MFA related: {state.get('sso_mfa_related', False)}
Related systems: {', '.join(state.get('related_systems', []))}"""

    # Add KB context if matches were found
    kb_matches = state.get("kb_matches", [])
    if kb_matches:
        context += "\n\nRelevant knowledge base articles found:"
        for i, match in enumerate(kb_matches, 1):
            context += f"\n  KB #{i}: {match.get('title', 'N/A')}"
            context += f"\n  Resolution: {match.get('resolution', 'N/A')}"

    response = call_claude(RESPONDER_PROMPT, context)

    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
    except json.JSONDecodeError:
        data = {
            "resolution_steps": ["Investigate the reported issue", "Apply standard troubleshooting", "Escalate if unresolved"],
            "response_draft": "Hi, we've received your ticket and are looking into it. We'll update you shortly.",
            "resolution_notes": "Auto-generated fallback — manual review needed."
        }

    return {
        "resolution_steps": data.get("resolution_steps", []),
        "response_draft": data.get("response_draft", ""),
        "resolution_notes": data.get("resolution_notes", ""),
    }


# ── Build the LangGraph pipeline ─────────────────────────────

def build_pipeline():
    """Build and compile the 3-agent LangGraph pipeline."""
    graph = StateGraph(TicketState)

    # Add the three agent nodes
    graph.add_node("classifier", classifier_agent)
    graph.add_node("kb_search", kb_search_agent)
    graph.add_node("responder", responder_agent)

    # Define the flow: classifier → kb_search → responder → END
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "kb_search")
    graph.add_edge("kb_search", "responder")
    graph.add_edge("responder", END)

    return graph.compile()


# ── Main entry point ─────────────────────────────────────────

def process_ticket(raw_text: str, requester: str = "Staff Member") -> dict:
    """Process a support ticket through the full pipeline and return results."""
    pipeline = build_pipeline()

    initial_state = {
        "raw_text": raw_text,
        "requester": requester,
        "category": None,
        "priority": None,
        "assigned_to": None,
        "subject": None,
        "related_systems": None,
        "sso_mfa_related": None,
        "estimated_time": None,
        "kb_matches": None,
        "kb_resolution_found": None,
        "resolution_steps": None,
        "response_draft": None,
        "resolution_notes": None,
    }

    result = pipeline.invoke(initial_state)
    return dict(result)