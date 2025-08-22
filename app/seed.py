from sqlalchemy.orm import Session
from datetime import date
from . import models

SAMPLE_ISSUERS = [
    {"name": "Acme Industries", "ticker": "ACME", "country": "IN"},
    {"name": "Bharat Power Ltd", "ticker": "BPL", "country": "IN"},
    {"name": "Global Finance PLC", "ticker": "GFIN", "country": "UK"},
]

SAMPLE_FUNDAMENTALS = [
    # name, report_date, revenue, ebitda, total_debt
    ("Acme Industries", date(2024, 12, 31), 1250.5, 210.2, 450.0),
    ("Acme Industries", date(2025, 3, 31), 310.4, 52.1, 440.0),
    ("Bharat Power Ltd", date(2024, 12, 31), 980.2, 150.3, 700.0),
    ("Global Finance PLC", date(2025, 3, 31), 220.0, 80.0, 120.0),
]

def seed_if_empty(db: Session) -> None:
    """
    Insert sample data if tables are empty. Idempotent on empty -> filled.
    """
    if db.query(models.Issuer).count() == 0:
        # Insert issuers and keep name->id mapping
        name_to_id = {}
        for row in SAMPLE_ISSUERS:
            obj = models.Issuer(**row)
            db.add(obj)
            db.flush()  # obtain obj.id before commit
            name_to_id[row["name"]] = obj.id

        # Insert fundamentals referencing issuer ids
        for name, rdate, rev, ebitda, debt in SAMPLE_FUNDAMENTALS:
            issuer_id = name_to_id.get(name)
            if issuer_id:
                db.add(models.Fundamental(
                    issuer_id=issuer_id,
                    report_date=rdate,
                    revenue=rev,
                    ebitda=ebitda,
                    total_debt=debt,
                ))
        db.commit()
