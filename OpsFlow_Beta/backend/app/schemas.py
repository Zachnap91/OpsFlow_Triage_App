from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["Safety", "IT", "Facilities", "People", "Supply Chain", "Quality", "Other"]
Priority = Literal["Low", "Medium", "High", "Critical"]
Status = Literal["New", "Under Review", "Approved", "In Progress", "Completed"]


class RequestCreate(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    description: str = Field(min_length=10, max_length=3000)
    requester: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)


class RequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=4, max_length=120)
    description: str | None = Field(default=None, min_length=10, max_length=3000)
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    owner: str | None = Field(default=None, max_length=100)
    actor: str = Field(default="Portfolio User", min_length=2, max_length=100)


class TriageApproval(BaseModel):
    category: Category
    priority: Priority
    actor: str = Field(default="Portfolio User", min_length=2, max_length=100)


class ActivityOut(BaseModel):
    id: int
    action: str
    actor: str
    detail: str
    created_at: datetime


class RequestOut(BaseModel):
    id: int
    title: str
    description: str
    requester: str
    department: str
    category: Category
    priority: Priority
    status: Status
    owner: str | None
    ai_summary: str | None
    ai_category: Category | None
    ai_priority: Priority | None
    ai_confidence: float | None
    triage_provider: str | None
    triage_approved: bool
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestOut):
    activity: list[ActivityOut]


class StatsOut(BaseModel):
    total: int
    open: int
    critical: int
    pending_approval: int
    by_status: dict[str, int]

