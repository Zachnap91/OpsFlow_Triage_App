from app.database import db, init_db
from app.main import create_request
from app.schemas import RequestCreate

SAMPLES = [
    RequestCreate(
        title="Production scheduling system unavailable",
        description="The assembly team cannot access the production scheduling system and work is blocked for the morning shift.",
        requester="Avery Chen",
        department="Manufacturing",
    ),
    RequestCreate(
        title="Receiving door safety sensor warning",
        description="The receiving door safety sensor intermittently reports a hazard and should be inspected before the next delivery.",
        requester="Morgan Reyes",
        department="Facilities",
    ),
    RequestCreate(
        title="New employee access workflow",
        description="Create a repeatable onboarding workflow for application access, training confirmation, and manager approval.",
        requester="Taylor Brooks",
        department="People Operations",
    ),
]

if __name__ == "__main__":
    init_db()
    with db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    if existing:
        print("Demo data not added because requests already exist.")
    else:
        for sample in SAMPLES:
            create_request(sample)
        print(f"Added {len(SAMPLES)} demo requests.")
