from datetime import datetime, timedelta


def build_mock_tickets() -> list[dict]:
    now = datetime.utcnow()
    return [
        {
            "ticket_no": f"TKT-{1000 + i}",
            "created_on": (now - timedelta(hours=i)).isoformat(),
            "customer": f"Client {i%3}",
            "product": "ERP",
            "remark": f"Issue {i}",
            "category": "Support",
            "status": "OPEN" if i < 10 else "CLOSED",
            "type": "SERVICE",
            "priority": "HIGH" if i % 4 == 0 else "MEDIUM",
            "assign_executive": 100 + (i % 5),
            "mobile": "9999999999",
            "contact": f"Contact {i}",
            "email": f"user{i}@example.com",
            "address": "Demo Street",
            "company": 1,
            "branch": 1,
            "department": 1,
            "attachments": [{"name": f"log_{i}.txt", "url": f"https://example.com/log_{i}.txt"}],
        }
        for i in range(15)
    ]
