import os

os.environ["OPERATIONS_DB_PATH"] = "/tmp/operations-triage-test.db"

from fastapi.testclient import TestClient

from app.database import DB_PATH
from app.main import app


def setup_module():
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_complete_request_workflow():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}

        created = client.post("/api/requests", json={
            "title": "Production network outage",
            "description": "The production network failed and the assembly team cannot access the scheduling system.",
            "requester": "Avery Chen",
            "department": "Manufacturing",
        })
        assert created.status_code == 201
        body = created.json()
        assert body["category"] == "IT"
        assert body["priority"] == "High"
        assert body["triage_approved"] is False

        approved = client.post(f"/api/requests/{body['id']}/approve-triage", json={
            "category": "IT", "priority": "Critical", "actor": "Jordan Lee"
        })
        assert approved.status_code == 200
        assert approved.json()["status"] == "Under Review"
        assert approved.json()["priority"] == "Critical"

        updated = client.patch(f"/api/requests/{body['id']}", json={
            "status": "In Progress", "owner": "Jordan Lee", "actor": "Jordan Lee"
        })
        assert updated.status_code == 200
        assert updated.json()["owner"] == "Jordan Lee"

        detail = client.get(f"/api/requests/{body['id']}").json()
        assert len(detail["activity"]) == 3

        stats = client.get("/api/stats").json()
        assert stats["total"] == 1
        assert stats["critical"] == 1


def test_validation_rejects_short_description():
    with TestClient(app) as client:
        response = client.post("/api/requests", json={
            "title": "Short title",
            "description": "Too short",
            "requester": "Avery Chen",
            "department": "IT",
        })
        assert response.status_code == 422

