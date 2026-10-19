from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.entities import Task


def create_follow_up_task(
    db: Session,
    organization_id: str,
    title: str,
    description: Optional[str] = None,
    lead_id: Optional[str] = None,
    call_id: Optional[str] = None,
    priority: str = "medium",
    due_in_hours: int = 24
) -> Task:
    """Creates an actionable CRM follow-up task linked to a lead or call."""
    due_date = datetime.now(timezone.utc) + timedelta(hours=due_in_hours)
    task = Task(
        organization_id=organization_id,
        lead_id=lead_id,
        call_id=call_id,
        title=title,
        description=description,
        priority=priority,
        status="pending",
        due_date=due_date
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
