from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import db, init_db
from .schemas import RequestCreate, RequestDetail, RequestOut, RequestUpdate, StatsOut, TriageApproval
from .triage import triage

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Operations Request and Triage API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def activity(conn: Any, request_id: int, action: str, actor: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO activity(request_id, action, actor, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (request_id, action, actor, detail, now()),
    )


def row_to_request(row: Any) -> dict[str, Any]:
    data = dict(row)
    data["triage_approved"] = bool(data["triage_approved"])
    return data


def get_request_or_404(conn: Any, request_id: int) -> Any:
    row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Request not found")
    return row


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/requests", response_model=list[RequestOut])
def list_requests(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = Query(default=None, max_length=100),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if status:
        clauses.append("status = ?"); values.append(status)
    if priority:
        clauses.append("priority = ?"); values.append(priority)
    if search:
        clauses.append("(title LIKE ? OR description LIKE ? OR requester LIKE ? OR department LIKE ?)")
        term = f"%{search}%"; values.extend([term, term, term, term])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with db() as conn:
        rows = conn.execute(f"SELECT * FROM requests{where} ORDER BY updated_at DESC", values).fetchall()
    return [row_to_request(row) for row in rows]


@app.post("/api/requests", response_model=RequestOut, status_code=201)
def create_request(payload: RequestCreate) -> dict[str, Any]:
    result = triage(payload.title, payload.description)
    timestamp = now()
    with db() as conn:
        cursor = conn.execute(
            """INSERT INTO requests(
                title, description, requester, department, category, priority, status,
                ai_summary, ai_category, ai_priority, ai_confidence, triage_provider,
                triage_approved, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'New', ?, ?, ?, ?, ?, 0, ?, ?)""",
            (payload.title, payload.description, payload.requester, payload.department,
             result.category, result.priority, result.summary, result.category,
             result.priority, result.confidence, result.provider, timestamp, timestamp),
        )
        request_id = cursor.lastrowid
        activity(conn, request_id, "Created", payload.requester, "Request submitted and automatically triaged")
        row = get_request_or_404(conn, request_id)
    return row_to_request(row)


@app.get("/api/requests/{request_id}", response_model=RequestDetail)
def get_request(request_id: int) -> dict[str, Any]:
    with db() as conn:
        row = get_request_or_404(conn, request_id)
        events = conn.execute("SELECT * FROM activity WHERE request_id = ? ORDER BY created_at DESC", (request_id,)).fetchall()
    data = row_to_request(row); data["activity"] = [dict(event) for event in events]
    return data


@app.patch("/api/requests/{request_id}", response_model=RequestOut)
def update_request(request_id: int, payload: RequestUpdate) -> dict[str, Any]:
    changes = payload.model_dump(exclude_none=True)
    actor = changes.pop("actor", "Portfolio User")
    if not changes:
        raise HTTPException(400, "No changes provided")
    with db() as conn:
        before = dict(get_request_or_404(conn, request_id))
        assignments = ", ".join(f"{field} = ?" for field in changes)
        conn.execute(f"UPDATE requests SET {assignments}, updated_at = ? WHERE id = ?", [*changes.values(), now(), request_id])
        detail = "; ".join(f"{field}: {before.get(field)} -> {value}" for field, value in changes.items())
        activity(conn, request_id, "Updated", actor, detail)
        row = get_request_or_404(conn, request_id)
    return row_to_request(row)


@app.post("/api/requests/{request_id}/approve-triage", response_model=RequestOut)
def approve_triage(request_id: int, payload: TriageApproval) -> dict[str, Any]:
    with db() as conn:
        get_request_or_404(conn, request_id)
        conn.execute(
            "UPDATE requests SET category = ?, priority = ?, triage_approved = 1, status = 'Under Review', updated_at = ? WHERE id = ?",
            (payload.category, payload.priority, now(), request_id),
        )
        activity(conn, request_id, "Triage approved", payload.actor, f"Category {payload.category}; priority {payload.priority}")
        row = get_request_or_404(conn, request_id)
    return row_to_request(row)


@app.get("/api/stats", response_model=StatsOut)
def stats() -> dict[str, Any]:
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        open_count = conn.execute("SELECT COUNT(*) FROM requests WHERE status != 'Completed'").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM requests WHERE priority = 'Critical' AND status != 'Completed'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM requests WHERE triage_approved = 0").fetchone()[0]
        status_rows = conn.execute("SELECT status, COUNT(*) count FROM requests GROUP BY status").fetchall()
    return {"total": total, "open": open_count, "critical": critical, "pending_approval": pending,
            "by_status": {row["status"]: row["count"] for row in status_rows}}

