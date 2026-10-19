from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass


@dataclass
class TriageResult:
    summary: str
    category: str
    priority: str
    confidence: float
    provider: str


CATEGORY_KEYWORDS = {
    "Safety": ["safety", "injury", "hazard", "emergency", "smoke", "fire", "danger"],
    "IT": ["software", "login", "computer", "network", "system", "api", "database", "error", "bug"],
    "Facilities": ["building", "door", "water", "leak", "heating", "light", "facility", "repair"],
    "People": ["employee", "staff", "training", "hiring", "schedule", "payroll", "benefits"],
    "Supply Chain": ["supplier", "inventory", "part", "shipment", "delivery", "material", "vendor"],
    "Quality": ["quality", "defect", "inspection", "nonconformance", "audit", "compliance"],
}

CRITICAL = ["emergency", "fire", "injury", "grounded", "production stopped", "security breach"]
HIGH = ["blocked", "outage", "cannot", "failed", "urgent", "deadline", "safety", "defect"]
LOW = ["suggestion", "nice to have", "when possible", "minor", "cosmetic"]


def _compact_summary(text: str, limit: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    first = re.split(r"(?<=[.!?])\s+", clean)[0]
    return first if len(first) <= limit else first[: limit - 1].rstrip() + "…"


def local_triage(title: str, description: str) -> TriageResult:
    text = f"{title} {description}".lower()
    scores = {category: sum(text.count(word) for word in words) for category, words in CATEGORY_KEYWORDS.items()}
    category, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        category = "Other"

    if any(word in text for word in CRITICAL):
        priority = "Critical"
    elif any(word in text for word in HIGH):
        priority = "High"
    elif any(word in text for word in LOW):
        priority = "Low"
    else:
        priority = "Medium"

    confidence = min(0.96, 0.58 + (score * 0.08)) if category != "Other" else 0.51
    return TriageResult(_compact_summary(description), category, priority, confidence, "local-rules")


def openai_triage(title: str, description: str) -> TriageResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return local_triage(title, description)

    prompt = {
        "title": title,
        "description": description,
        "task": "Return JSON with summary, category, priority, confidence. Category must be Safety, IT, Facilities, People, Supply Chain, Quality, or Other. Priority must be Low, Medium, High, or Critical. Confidence is 0 to 1.",
    }
    payload = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        "input": json.dumps(prompt),
        "text": {"format": {"type": "json_object"}},
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read())
        parsed = json.loads(body["output"][0]["content"][0]["text"])
        return TriageResult(
            str(parsed["summary"])[:300],
            str(parsed["category"]),
            str(parsed["priority"]),
            float(parsed["confidence"]),
            f"openai:{os.getenv('OPENAI_MODEL', 'gpt-5-mini')}",
        )
    except Exception:
        result = local_triage(title, description)
        result.provider = "local-rules-fallback"
        return result


def triage(title: str, description: str) -> TriageResult:
    return openai_triage(title, description)

