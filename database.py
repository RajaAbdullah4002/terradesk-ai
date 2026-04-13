"""TerraDesk AI — SQLite database layer for tickets, knowledge base, and activity log."""

import sqlite3
import json
from datetime import datetime

DB_PATH = "terradesk.db"


def get_conn():
    """Get a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_ref TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            assigned_to TEXT,
            requester TEXT,
            resolution_steps TEXT,
            resolution_notes TEXT,
            estimated_time TEXT,
            related_systems TEXT,
            sso_mfa_related INTEGER DEFAULT 0,
            freshdesk_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            resolution TEXT NOT NULL,
            systems TEXT,
            times_used INTEGER DEFAULT 0,
            created_from_ticket TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_ref TEXT,
            action TEXT NOT NULL,
            details TEXT,
            performed_by TEXT DEFAULT 'AI Agent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def generate_ticket_ref():
    """Generate a unique ticket reference like TF-20260412-001."""
    conn = get_conn()
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"TF-{today}"

    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE ticket_ref LIKE ?",
        (f"{prefix}%",)
    ).fetchone()

    count = row["cnt"] + 1
    conn.close()
    return f"{prefix}-{count:03d}"


# ── Ticket CRUD ──────────────────────────────────────────────


def create_ticket(subject, description, requester="Staff Member",
                  category=None, priority="Medium", assigned_to=None,
                  resolution_steps=None, estimated_time=None,
                  related_systems=None, sso_mfa_related=False,
                  freshdesk_id=None):
    """Insert a new ticket and return its reference."""
    conn = get_conn()
    ticket_ref = generate_ticket_ref()

    conn.execute("""
        INSERT INTO tickets
        (ticket_ref, subject, description, requester, category, priority,
         assigned_to, resolution_steps, estimated_time, related_systems,
         sso_mfa_related, freshdesk_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_ref, subject, description, requester, category, priority,
        assigned_to,
        json.dumps(resolution_steps) if resolution_steps else None,
        estimated_time,
        json.dumps(related_systems) if related_systems else None,
        1 if sso_mfa_related else 0,
        freshdesk_id
    ))

    log_activity(ticket_ref, "CREATED", f"Ticket created — {subject}", conn=conn)
    conn.commit()
    conn.close()
    return ticket_ref


def get_ticket(ticket_ref):
    """Fetch a single ticket by reference."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM tickets WHERE ticket_ref = ?", (ticket_ref,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_tickets(status=None, category=None, limit=50):
    """Fetch tickets with optional filters."""
    conn = get_conn()
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_ticket(ticket_ref, **kwargs):
    """Update ticket fields dynamically."""
    conn = get_conn()
    allowed = [
        "subject", "description", "category", "priority", "status",
        "assigned_to", "resolution_steps", "resolution_notes",
        "estimated_time", "related_systems", "sso_mfa_related"
    ]

    sets = []
    params = []
    for key, value in kwargs.items():
        if key in allowed:
            if key in ("resolution_steps", "related_systems") and isinstance(value, list):
                value = json.dumps(value)
            sets.append(f"{key} = ?")
            params.append(value)

    if not sets:
        conn.close()
        return

    sets.append("updated_at = ?")
    params.append(datetime.now().isoformat())

    if kwargs.get("status") == "Resolved":
        sets.append("resolved_at = ?")
        params.append(datetime.now().isoformat())

    params.append(ticket_ref)

    conn.execute(
        f"UPDATE tickets SET {', '.join(sets)} WHERE ticket_ref = ?",
        params
    )

    changes = ", ".join(f"{k}={v}" for k, v in kwargs.items() if k in allowed)
    log_activity(ticket_ref, "UPDATED", changes, conn=conn)
    conn.commit()
    conn.close()


# ── Knowledge Base ───────────────────────────────────────────


def add_kb_article(title, category, symptoms, resolution, systems=None,
                   created_from_ticket=None):
    """Add an article to the knowledge base."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO knowledge_base
        (title, category, symptoms, resolution, systems, created_from_ticket)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title, category, symptoms, resolution,
        json.dumps(systems) if systems else None,
        created_from_ticket
    ))
    conn.commit()
    conn.close()


def search_kb(query, category=None, limit=5):
    """Search knowledge base articles by keyword matching."""
    conn = get_conn()
    sql = """
        SELECT * FROM knowledge_base
        WHERE (symptoms LIKE ? OR title LIKE ? OR resolution LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY times_used DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def increment_kb_usage(article_id):
    """Increment the usage counter for a KB article."""
    conn = get_conn()
    conn.execute(
        "UPDATE knowledge_base SET times_used = times_used + 1 WHERE id = ?",
        (article_id,)
    )
    conn.commit()
    conn.close()


def get_all_kb_articles(category=None):
    """Fetch all knowledge base articles."""
    conn = get_conn()
    if category:
        rows = conn.execute(
            "SELECT * FROM knowledge_base WHERE category = ? ORDER BY times_used DESC",
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM knowledge_base ORDER BY times_used DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Activity Log ─────────────────────────────────────────────


def log_activity(ticket_ref, action, details, performed_by="AI Agent", conn=None):
    """Log an activity against a ticket."""
    close = False
    if conn is None:
        conn = get_conn()
        close = True

    conn.execute("""
        INSERT INTO activity_log (ticket_ref, action, details, performed_by)
        VALUES (?, ?, ?, ?)
    """, (ticket_ref, action, details, performed_by))

    if close:
        conn.commit()
        conn.close()


def get_ticket_activity(ticket_ref):
    """Get all activity for a specific ticket."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM activity_log WHERE ticket_ref = ? ORDER BY created_at DESC",
        (ticket_ref,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Analytics Queries ────────────────────────────────────────


def get_ticket_stats():
    """Get summary statistics for the dashboard."""
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) as cnt FROM tickets").fetchone()["cnt"]
    open_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE status = 'Open'"
    ).fetchone()["cnt"]
    in_progress = conn.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE status = 'In Progress'"
    ).fetchone()["cnt"]
    resolved = conn.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE status = 'Resolved'"
    ).fetchone()["cnt"]

    by_category = conn.execute("""
        SELECT category, COUNT(*) as cnt FROM tickets
        WHERE category IS NOT NULL
        GROUP BY category ORDER BY cnt DESC
    """).fetchall()

    by_priority = conn.execute("""
        SELECT priority, COUNT(*) as cnt FROM tickets
        GROUP BY priority ORDER BY cnt DESC
    """).fetchall()

    by_assignee = conn.execute("""
        SELECT assigned_to, COUNT(*) as cnt FROM tickets
        WHERE assigned_to IS NOT NULL
        GROUP BY assigned_to ORDER BY cnt DESC
    """).fetchall()

    recent = conn.execute("""
        SELECT * FROM tickets ORDER BY created_at DESC LIMIT 5
    """).fetchall()

    conn.close()

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "by_category": [dict(r) for r in by_category],
        "by_priority": [dict(r) for r in by_priority],
        "by_assignee": [dict(r) for r in by_assignee],
        "recent": [dict(r) for r in recent],
    }