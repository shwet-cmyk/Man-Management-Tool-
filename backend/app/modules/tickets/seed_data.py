from datetime import datetime, timedelta


def sample_ticket_seeds():
    now = datetime.utcnow()
    return [
        {"subject": "High near breach", "priority": "HIGH", "status": "IN_PROGRESS", "created_on": now - timedelta(hours=20)},
        {"subject": "High breached", "priority": "HIGH", "status": "IN_PROGRESS", "created_on": now - timedelta(hours=40)},
        {"subject": "Medium awaiting response", "priority": "MEDIUM", "status": "OPEN", "created_on": now - timedelta(hours=10)},
        {"subject": "Low closed in SLA", "priority": "LOW", "status": "CLOSED", "created_on": now - timedelta(days=2)},
        {"subject": "Reopened ticket", "priority": "MEDIUM", "status": "REOPENED", "created_on": now - timedelta(days=1)},
        {"subject": "Paused waiting customer", "priority": "LOW", "status": "WAITING_FOR_CUSTOMER", "created_on": now - timedelta(hours=30)},
    ]
