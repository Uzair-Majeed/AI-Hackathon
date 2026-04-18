"""
SQLite database layer — persist parsed opportunities and runs for demo replay.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional
from models.schemas import Opportunity, StudentProfile

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            email_count INTEGER NOT NULL,
            opportunity_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            email_index INTEGER NOT NULL,
            title TEXT,
            opp_type TEXT,
            deadline TEXT,
            deadline_raw TEXT,
            eligibility_json TEXT,
            required_documents_json TEXT,
            location TEXT,
            link TEXT,
            contact TEXT,
            organization TEXT,
            stipend_or_amount TEXT,
            profile_match_score REAL,
            urgency_score REAL,
            preference_score REAL,
            completeness_score REAL,
            value_score REAL,
            final_score REAL,
            rank INTEGER,
            why TEXT,
            requirements_summary TEXT,
            checklist_json TEXT,
            classification_reason TEXT,
            raw_email TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );
    """)
    conn.commit()
    conn.close()


def save_run(
    profile: StudentProfile,
    opportunities: List[Opportunity],
    total_emails: int,
) -> int:
    """Save a pipeline run and its opportunities. Returns the run_id."""
    conn = _get_conn()

    profile_dict = {
        "degree": profile.degree,
        "program": profile.program,
        "semester": profile.semester,
        "cgpa": profile.cgpa,
        "skills": profile.skills,
        "interests": profile.interests,
        "preferred_types": profile.preferred_types,
        "financial_need": profile.financial_need,
        "location_preference": profile.location_preference,
        "past_experience": profile.past_experience,
    }

    cursor = conn.execute(
        """INSERT INTO runs (timestamp, profile_json, email_count, opportunity_count)
           VALUES (?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            json.dumps(profile_dict),
            total_emails,
            len(opportunities),
        ),
    )
    run_id = cursor.lastrowid

    for opp in opportunities:
        conn.execute(
            """INSERT INTO opportunities (
                run_id, email_index, title, opp_type, deadline, deadline_raw,
                eligibility_json, required_documents_json, location, link, contact,
                organization, stipend_or_amount,
                profile_match_score, urgency_score, preference_score,
                completeness_score, value_score, final_score, rank,
                why, requirements_summary, checklist_json,
                classification_reason, raw_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                opp.email_index,
                opp.title,
                opp.opp_type,
                opp.deadline.isoformat() if opp.deadline else None,
                opp.deadline_raw,
                json.dumps(opp.eligibility),
                json.dumps(opp.required_documents),
                opp.location,
                opp.link,
                opp.contact,
                opp.organization,
                opp.stipend_or_amount,
                opp.profile_match_score,
                opp.urgency_score,
                opp.preference_score,
                opp.completeness_score,
                opp.value_score,
                opp.final_score,
                opp.rank,
                opp.why,
                opp.requirements_summary,
                json.dumps(opp.checklist),
                opp.classification_reason,
                opp.raw_email,
            ),
        )

    conn.commit()
    conn.close()
    return run_id


# ──────────────────────────────────────────
# Email + Config tables (new Gmail-themed UI)
# ──────────────────────────────────────────

def init_emails_table():
    """Create emails and config tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT NOT NULL,
            subject_snippet TEXT DEFAULT '',
            sender_snippet TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            added_at TEXT NOT NULL,
            spam_reason TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            profile_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def _extract_header(raw_text: str, header: str) -> str:
    """Extract a header value from raw email text (first 10 lines)."""
    for line in raw_text.split('\n')[:10]:
        if line.lower().startswith(header.lower() + ':'):
            return line[len(header) + 1:].strip()[:120]
    return ''


def add_email(raw_text: str) -> int:
    """Insert a new email as pending. Returns its DB id."""
    subject = _extract_header(raw_text, 'Subject')
    sender  = _extract_header(raw_text, 'From')
    conn = _get_conn()
    cursor = conn.execute(
        "INSERT INTO emails (raw_text, subject_snippet, sender_snippet, status, added_at) VALUES (?, ?, ?, 'pending', ?)",
        (raw_text, subject, sender, datetime.now().isoformat()),
    )
    eid = cursor.lastrowid
    conn.commit()
    conn.close()
    return eid


def get_all_emails() -> list:
    """Return all emails ordered newest first."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM emails ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_emails_by_status(status: str) -> list:
    """Return emails filtered by status."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM emails WHERE status = ? ORDER BY id ASC", (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_email_status(email_id: int, status: str, spam_reason: str = ""):
    """Update an email's classification status."""
    conn = _get_conn()
    conn.execute(
        "UPDATE emails SET status = ?, spam_reason = ? WHERE id = ?",
        (status, spam_reason, email_id),
    )
    conn.commit()
    conn.close()


def reset_all_email_statuses():
    """Reset all emails to pending and wipe run/opportunity history."""
    conn = _get_conn()
    conn.execute("UPDATE emails SET status = 'pending', spam_reason = ''")
    conn.execute("DELETE FROM opportunities")
    conn.execute("DELETE FROM runs")
    conn.commit()
    conn.close()


def delete_all_emails():
    """Delete every email from the emails table."""
    conn = _get_conn()
    conn.execute("DELETE FROM emails")
    conn.execute("DELETE FROM opportunities")
    conn.execute("DELETE FROM runs")
    conn.commit()
    conn.close()


def get_email_counts() -> dict:
    """Return counts keyed by status."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM emails GROUP BY status"
    ).fetchall()
    conn.close()
    result = {'pending': 0, 'opportunity': 0, 'spam': 0}
    for r in rows:
        result[r['status']] = r['cnt']
    return result


def has_any_emails() -> bool:
    """True if at least one email exists."""
    conn = _get_conn()
    cnt = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    conn.close()
    return cnt > 0


def save_config(profile_dict: dict):
    """Upsert the student profile configuration."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO config (id, profile_json, updated_at) VALUES (1, ?, ?)",
        (json.dumps(profile_dict), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_config() -> Optional[dict]:
    """Retrieve saved configuration, or None if not set."""
    conn = _get_conn()
    row = conn.execute("SELECT profile_json FROM config WHERE id = 1").fetchone()
    conn.close()
    return json.loads(row['profile_json']) if row else None


def get_opportunity_by_email_text(raw_text: str) -> Optional[dict]:
    """Look up a stored opportunity by matching raw email text."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM opportunities WHERE raw_email = ? ORDER BY id DESC LIMIT 1",
        (raw_text,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    # Deserialise JSON fields
    for key in ('eligibility_json', 'required_documents_json', 'checklist_json'):
        try:
            d[key] = json.loads(d.get(key) or '[]')
        except Exception:
            d[key] = []
    return d


def get_last_run() -> Optional[dict]:
    """Retrieve the most recent run with its opportunities."""
    conn = _get_conn()

    run_row = conn.execute(
        "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not run_row:
        conn.close()
        return None

    run_id = run_row["id"]
    opp_rows = conn.execute(
        "SELECT * FROM opportunities WHERE run_id = ? ORDER BY rank ASC",
        (run_id,),
    ).fetchall()

    conn.close()

    opportunities = []
    for row in opp_rows:
        opp = Opportunity(
            email_index=row["email_index"],
            raw_email=row["raw_email"] or "",
        )
        opp.title = row["title"] or "Untitled"
        opp.opp_type = row["opp_type"] or "other"
        opp.deadline_raw = row["deadline_raw"] or ""
        opp.deadline = datetime.fromisoformat(row["deadline"]) if row["deadline"] else None
        opp.eligibility = json.loads(row["eligibility_json"] or "[]")
        opp.required_documents = json.loads(row["required_documents_json"] or "[]")
        opp.location = row["location"] or ""
        opp.link = row["link"] or ""
        opp.contact = row["contact"] or ""
        opp.organization = row["organization"] or ""
        opp.stipend_or_amount = row["stipend_or_amount"] or ""
        opp.profile_match_score = row["profile_match_score"] or 0.0
        opp.urgency_score = row["urgency_score"] or 0.0
        opp.preference_score = row["preference_score"] or 0.0
        opp.completeness_score = row["completeness_score"] or 0.0
        opp.value_score = row["value_score"] or 0.0
        opp.final_score = row["final_score"] or 0.0
        opp.rank = row["rank"] or 0
        opp.why = row["why"] or ""
        opp.requirements_summary = row["requirements_summary"] or ""
        opp.checklist = json.loads(row["checklist_json"] or "[]")
        opp.classification_reason = row["classification_reason"] or ""
        opportunities.append(opp)

    return {
        "run_id": run_id,
        "timestamp": run_row["timestamp"],
        "profile": json.loads(run_row["profile_json"]),
        "email_count": run_row["email_count"],
        "opportunity_count": run_row["opportunity_count"],
        "opportunities": opportunities,
    }
