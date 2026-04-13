"""TerraDesk AI — IT Support Intelligence Platform for Terra Firma Business Consulting."""

import streamlit as st
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from database import (
    init_db, create_ticket, get_all_tickets, get_ticket,
    update_ticket, get_ticket_stats, get_all_kb_articles,
    search_kb, get_ticket_activity, add_kb_article
)

# ── Page config ──────────────────────────────────────────────

st.set_page_config(
    page_title="TerraDesk AI — IT Support Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database on first run
init_db()


# ── Custom CSS ───────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 700;
        color: #1B3A6B;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 14px;
        color: #666;
        margin-top: -10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid #1B3A6B;
    }
    .priority-critical { color: #C50F1F; font-weight: 700; }
    .priority-high { color: #E74856; font-weight: 700; }
    .priority-medium { color: #C4A000; font-weight: 600; }
    .priority-low { color: #2D7D46; font-weight: 600; }
    .status-open { color: #0078D4; }
    .status-progress { color: #FF8C00; }
    .status-resolved { color: #2D7D46; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ──────────────────────────────────────

st.sidebar.image("https://b2606367.smushcdn.com/2606367/wp-content/uploads/2021/06/terrafirma-e1623647432779.png", width=200)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🎯 New Ticket", "📋 All Tickets", "📚 Knowledge Base", "🔌 Freshdesk Sync"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**IT Team**")
st.sidebar.markdown("🔧 Blair Douglass — Systems Engineer")
st.sidebar.markdown("☁️ Carolyn Hayward — IT Digital Lead")
st.sidebar.markdown("---")
st.sidebar.caption("Built by Roger (Raja Abdullah)")
st.sidebar.caption("rajaabdullah.com")


# ── Helper functions ─────────────────────────────────────────

def priority_color(priority):
    """Return a color for the priority level."""
    colors = {"Critical": "#C50F1F", "High": "#E74856", "Medium": "#C4A000", "Low": "#2D7D46"}
    return colors.get(priority, "#666")


def status_emoji(status):
    """Return an emoji for the ticket status."""
    emojis = {"Open": "🔵", "In Progress": "🟡", "Resolved": "🟢"}
    return emojis.get(status, "⚪")


def parse_json_field(value):
    """Safely parse a JSON string field from the database."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# ══════════════════════════════════════════════════════════════
# PAGE 1: DASHBOARD
# ══════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 IT Support Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Terra Firma Business Consulting — Real-time ticket overview</p>', unsafe_allow_html=True)
    st.markdown("")

    stats = get_ticket_stats()

    # ── Metric cards row ─────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tickets", stats["total"])
    with col2:
        st.metric("Open", stats["open"], delta=None)
    with col3:
        st.metric("In Progress", stats["in_progress"])
    with col4:
        st.metric("Resolved", stats["resolved"])

    st.markdown("---")

    # ── Charts row ───────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Tickets by Category")
        if stats["by_category"]:
            fig_cat = px.pie(
                values=[c["cnt"] for c in stats["by_category"]],
                names=[c["category"] for c in stats["by_category"]],
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig_cat.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No ticket data yet.")

    with chart_col2:
        st.subheader("Tickets by Priority")
        if stats["by_priority"]:
            priority_colors_map = {"Critical": "#C50F1F", "High": "#E74856", "Medium": "#C4A000", "Low": "#2D7D46"}
            fig_pri = px.bar(
                x=[p["priority"] for p in stats["by_priority"]],
                y=[p["cnt"] for p in stats["by_priority"]],
                color=[p["priority"] for p in stats["by_priority"]],
                color_discrete_map=priority_colors_map,
            )
            fig_pri.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Count",
            )
            st.plotly_chart(fig_pri, use_container_width=True)
        else:
            st.info("No ticket data yet.")

    # ── Team workload ────────────────────────────────────────
    st.markdown("---")
    st.subheader("Team Workload")

    if stats["by_assignee"]:
        work_col1, work_col2 = st.columns(2)
        for i, assignee in enumerate(stats["by_assignee"]):
            col = work_col1 if i % 2 == 0 else work_col2
            with col:
                name = assignee["assigned_to"] or "Unassigned"
                count = assignee["cnt"]
                st.markdown(f"**{name}** — {count} ticket{'s' if count != 1 else ''}")
                st.progress(min(count / max(stats["total"], 1), 1.0))

    # ── Recent tickets ───────────────────────────────────────
    st.markdown("---")
    st.subheader("Recent Tickets")

    if stats["recent"]:
        for t in stats["recent"]:
            emoji = status_emoji(t["status"])
            color = priority_color(t.get("priority", "Medium"))
            st.markdown(
                f"{emoji} **{t['ticket_ref']}** — {t['subject']} "
                f"<span style='color:{color}'>●{t.get('priority', 'Medium')}</span> "
                f"→ {t.get('assigned_to', 'Unassigned')}",
                unsafe_allow_html=True,
            )
    else:
        st.info("No tickets yet. Create one from the New Ticket page.")


# ══════════════════════════════════════════════════════════════
# PAGE 2: NEW TICKET (AI-powered)
# ══════════════════════════════════════════════════════════════

elif page == "🎯 New Ticket":
    st.markdown('<p class="main-header">🎯 Submit New Ticket</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered classification, routing, and resolution</p>', unsafe_allow_html=True)
    st.markdown("")

    # ── Input form ───────────────────────────────────────────
    with st.form("new_ticket_form"):
        requester = st.text_input("Your Name", placeholder="e.g., Sarah Chen")

        description = st.text_area(
            "Describe your issue",
            placeholder="e.g., I can't log into Teams after changing my phone. The authenticator app isn't set up on my new device.",
            height=120,
        )

        # Sample tickets for quick testing
        st.markdown("**Quick fill — sample issues:**")
        sample_col1, sample_col2 = st.columns(2)
        with sample_col1:
            st.caption("• Can't log in after getting a new phone")
            st.caption("• Need to set up a new Salesforce account for a consultant")
            st.caption("• My laptop says it's not compliant")
            st.caption("• Got a suspicious email pretending to be from Microsoft")
        with sample_col2:
            st.caption("• Accidentally deleted a SharePoint folder")
            st.caption("• Wi-Fi keeps dropping in the meeting room")
            st.caption("• New consultant starting Monday — full onboarding needed")
            st.caption("• Can't import rate cards into Salesforce price book")

        submitted = st.form_submit_button("🚀 Submit & Classify with AI", use_container_width=True)

    if submitted and description:
        try:
            has_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        except:
            has_key = os.getenv("ANTHROPIC_API_KEY")
        if not has_key:
            st.error("⚠️ ANTHROPIC_API_KEY not set. Add it to your environment or .streamlit/secrets.toml")
        else:
            with st.spinner("🤖 AI Pipeline: Classifier → KB Search → Responder..."):
                from pipeline import process_ticket

                result = process_ticket(
                    raw_text=description,
                    requester=requester or "Staff Member",
                )

            # Save to database
            ticket_ref = create_ticket(
                subject=result.get("subject", description[:50]),
                description=description,
                requester=requester or "Staff Member",
                category=result.get("category"),
                priority=result.get("priority", "Medium"),
                assigned_to=result.get("assigned_to"),
                resolution_steps=result.get("resolution_steps"),
                estimated_time=result.get("estimated_time"),
                related_systems=result.get("related_systems"),
                sso_mfa_related=result.get("sso_mfa_related", False),
            )

            # ── Display results ──────────────────────────────
            st.success(f"✅ Ticket created: **{ticket_ref}**")

            # Classification
            st.markdown("### 🏷️ Classification")
            class_col1, class_col2, class_col3 = st.columns(3)
            with class_col1:
                st.markdown(f"**Category:** {result.get('category', 'N/A')}")
            with class_col2:
                p = result.get('priority', 'Medium')
                st.markdown(f"**Priority:** <span style='color:{priority_color(p)}'>● {p}</span>", unsafe_allow_html=True)
            with class_col3:
                st.markdown(f"**Assigned to:** {result.get('assigned_to', 'N/A')}")

            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**Estimated time:** {result.get('estimated_time', 'N/A')}")
            with info_col2:
                if result.get("sso_mfa_related"):
                    st.warning("🔐 SSO/MFA related — Conditional Access review may be needed")

            # Related systems
            systems = result.get("related_systems", [])
            if systems:
                st.markdown(f"**Affected systems:** {', '.join(systems)}")

            # KB matches
            st.markdown("---")
            st.markdown("### 📚 Knowledge Base Matches")
            kb_matches = result.get("kb_matches", [])
            if kb_matches:
                for match in kb_matches:
                    with st.expander(f"📄 {match['title']} (used {match.get('times_used', 0)} times)"):
                        st.markdown(f"**Category:** {match['category']}")
                        st.markdown(f"**Symptoms:** {match['symptoms']}")
                        st.markdown(f"**Resolution:** {match['resolution']}")
            else:
                st.info("No matching KB articles found. This may be a new issue type.")

            # Resolution steps
            st.markdown("---")
            st.markdown("### 🔧 AI-Generated Resolution")
            steps = result.get("resolution_steps", [])
            if steps:
                for i, step in enumerate(steps, 1):
                    st.markdown(f"**Step {i}.** {step}")

            # Response draft
            st.markdown("---")
            st.markdown("### ✉️ Response Draft")
            response_draft = result.get("response_draft", "")
            if response_draft:
                st.text_area("Copy and send to the requester:", value=response_draft, height=150)

            # Internal notes
            notes = result.get("resolution_notes", "")
            if notes:
                st.markdown("### 📝 Internal Notes")
                st.info(notes)

    elif submitted and not description:
        st.warning("Please describe the issue before submitting.")


# ══════════════════════════════════════════════════════════════
# PAGE 3: ALL TICKETS
# ══════════════════════════════════════════════════════════════

elif page == "📋 All Tickets":
    st.markdown('<p class="main-header">📋 All Tickets</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">View, filter, and manage support tickets</p>', unsafe_allow_html=True)
    st.markdown("")

    # ── Filters ──────────────────────────────────────────────
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Open", "In Progress", "Resolved"])
    with filter_col2:
        category_filter = st.selectbox("Filter by Category", [
            "All", "Microsoft 365", "Salesforce", "Intune / Device",
            "SharePoint / Files", "Security / Access", "Network / Hardware",
            "Onboarding / Offboarding"
        ])

    tickets = get_all_tickets(
        status=status_filter if status_filter != "All" else None,
        category=category_filter if category_filter != "All" else None,
    )

    if tickets:
        st.markdown(f"**Showing {len(tickets)} ticket{'s' if len(tickets) != 1 else ''}**")
        st.markdown("")

        for t in tickets:
            emoji = status_emoji(t["status"])
            color = priority_color(t.get("priority", "Medium"))

            with st.expander(
                f"{emoji} {t['ticket_ref']} — {t['subject']} "
                f"[{t.get('priority', 'Medium')}] → {t.get('assigned_to', 'Unassigned')}"
            ):
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    st.markdown(f"**Requester:** {t.get('requester', 'N/A')}")
                    st.markdown(f"**Category:** {t.get('category', 'N/A')}")
                    st.markdown(f"**Priority:** {t.get('priority', 'N/A')}")
                    st.markdown(f"**Status:** {t['status']}")
                with detail_col2:
                    st.markdown(f"**Assigned to:** {t.get('assigned_to', 'N/A')}")
                    st.markdown(f"**Estimated time:** {t.get('estimated_time', 'N/A')}")
                    st.markdown(f"**Created:** {t.get('created_at', 'N/A')}")
                    if t.get("sso_mfa_related"):
                        st.warning("🔐 SSO/MFA Related")

                st.markdown(f"**Description:** {t['description']}")

                # Show resolution steps
                steps = parse_json_field(t.get("resolution_steps"))
                if steps:
                    st.markdown("**Resolution Steps:**")
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"{i}. {step}")

                # Status update buttons
                st.markdown("---")
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if t["status"] != "In Progress":
                        if st.button("🟡 Mark In Progress", key=f"prog_{t['ticket_ref']}"):
                            update_ticket(t["ticket_ref"], status="In Progress")
                            st.rerun()
                with btn_col2:
                    if t["status"] != "Resolved":
                        if st.button("🟢 Mark Resolved", key=f"resolve_{t['ticket_ref']}"):
                            update_ticket(t["ticket_ref"], status="Resolved")
                            st.rerun()
                with btn_col3:
                    if t["status"] == "Resolved":
                        if st.button("📚 Save to KB", key=f"kb_{t['ticket_ref']}"):
                            steps_text = " ".join(steps) if steps else "See ticket for details."
                            add_kb_article(
                                title=t["subject"],
                                category=t.get("category", "General"),
                                symptoms=t["description"][:200],
                                resolution=steps_text,
                                systems=parse_json_field(t.get("related_systems")),
                                created_from_ticket=t["ticket_ref"],
                            )
                            st.success("Added to Knowledge Base!")
    else:
        st.info("No tickets match your filters.")


# ══════════════════════════════════════════════════════════════
# PAGE 4: KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════

elif page == "📚 Knowledge Base":
    st.markdown('<p class="main-header">📚 Knowledge Base</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Searchable library of resolved issues and solutions</p>', unsafe_allow_html=True)
    st.markdown("")

    # ── Search ───────────────────────────────────────────────
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("Search knowledge base", placeholder="e.g., MFA, password reset, Salesforce...")
    with search_col2:
        kb_category = st.selectbox("Category", [
            "All", "Microsoft 365", "Salesforce", "Intune / Device",
            "SharePoint / Files", "Security / Access", "Network / Hardware",
            "Onboarding / Offboarding"
        ])

    # Get articles
    if search_query:
        articles = search_kb(
            search_query,
            category=kb_category if kb_category != "All" else None,
        )
    else:
        articles = get_all_kb_articles(
            category=kb_category if kb_category != "All" else None,
        )

    st.markdown(f"**{len(articles)} article{'s' if len(articles) != 1 else ''} found**")
    st.markdown("")

    if articles:
        for article in articles:
            with st.expander(f"📄 {article['title']} — used {article.get('times_used', 0)} times"):
                st.markdown(f"**Category:** {article['category']}")
                st.markdown(f"**Symptoms:** {article['symptoms']}")
                st.markdown("---")
                st.markdown(f"**Resolution:**")
                st.markdown(article['resolution'])

                systems = parse_json_field(article.get("systems"))
                if systems:
                    st.markdown(f"**Related systems:** {', '.join(systems)}")

                if article.get("created_from_ticket"):
                    st.caption(f"Created from ticket: {article['created_from_ticket']}")
    else:
        st.info("No articles found. Try a different search term or category.")

    # ── Add new article ──────────────────────────────────────
    st.markdown("---")
    st.subheader("Add New Article")

    with st.form("add_kb_form"):
        new_title = st.text_input("Title")
        new_category = st.selectbox("Category", [
            "Microsoft 365", "Salesforce", "Intune / Device",
            "SharePoint / Files", "Security / Access", "Network / Hardware",
            "Onboarding / Offboarding"
        ], key="new_kb_cat")
        new_symptoms = st.text_area("Symptoms / Keywords", height=80)
        new_resolution = st.text_area("Resolution Steps", height=120)

        if st.form_submit_button("💾 Save Article"):
            if new_title and new_symptoms and new_resolution:
                add_kb_article(
                    title=new_title,
                    category=new_category,
                    symptoms=new_symptoms,
                    resolution=new_resolution,
                )
                st.success(f"Article '{new_title}' added to Knowledge Base!")
                st.rerun()
            else:
                st.warning("Please fill in all fields.")


# ══════════════════════════════════════════════════════════════
# PAGE 5: FRESHDESK SYNC
# ══════════════════════════════════════════════════════════════

elif page == "🔌 Freshdesk Sync":
    st.markdown('<p class="main-header">🔌 Freshdesk Integration</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Connect to Freshdesk to sync tickets with an external ticketing system</p>', unsafe_allow_html=True)
    st.markdown("")

    st.info("""
    **Freshdesk** is a cloud-based IT ticketing platform widely used by Australian businesses.
    This integration lets TerraDesk AI pull tickets from Freshdesk, classify them with AI,
    and push resolution updates back.
    """)

    # ── Connection settings ──────────────────────────────────
    st.subheader("Connection Settings")

    fd_col1, fd_col2 = st.columns(2)
    with fd_col1:
        fd_domain = st.text_input("Freshdesk Domain", placeholder="e.g., terrafirma")
        st.caption("Your subdomain from terrafirma.freshdesk.com")
    with fd_col2:
        fd_api_key = st.text_input("API Key", type="password", placeholder="Your Freshdesk API key")
        st.caption("Found in Freshdesk → Profile Settings → API Key")

    if st.button("🔗 Test Connection"):
        if fd_domain and fd_api_key:
            from freshdesk_client import FreshdeskClient
            client = FreshdeskClient(fd_domain, fd_api_key)

            with st.spinner("Testing connection..."):
                if client.test_connection():
                    st.success("✅ Connected to Freshdesk successfully!")

                    # Fetch and display recent tickets
                    tickets = client.get_tickets(per_page=5)
                    if tickets:
                        st.subheader(f"Recent Freshdesk Tickets ({len(tickets)})")
                        for t in tickets:
                            status = client.map_status_from_freshdesk(t.get("status", 2))
                            priority = client.map_priority_from_freshdesk(t.get("priority", 2))
                            st.markdown(
                                f"**#{t['id']}** — {t.get('subject', 'No subject')} "
                                f"[{priority}] ({status})"
                            )
                else:
                    st.error("❌ Connection failed. Check your domain and API key.")
        else:
            st.warning("Please enter both domain and API key.")

    # ── How to set up Freshdesk ──────────────────────────────
    st.markdown("---")
    st.subheader("Setup Guide")
    st.markdown("""
    1. **Sign up** for a free Freshdesk account at [freshdesk.com](https://freshdesk.com)
    2. **Get your API key:** Profile icon → Profile Settings → Your API Key
    3. **Enter your domain** — if your URL is `mycompany.freshdesk.com`, the domain is `mycompany`
    4. **Test the connection** above
    5. Once connected, you can pull tickets from Freshdesk, classify them with AI, and push updates back

    The free plan supports up to 2 agents — perfect for a demo environment.
    """)