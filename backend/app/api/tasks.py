from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_tenant
from backend.app.models.entities import Task

router = APIRouter(prefix="/tasks", tags=["Follow-up Tasks"])


class UpdateTaskStatusRequest(BaseModel):
    status: str  # pending, in_progress, completed


@router.get("")
def list_tasks(
    status: Optional[str] = None,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(Task).filter(Task.organization_id == org_id)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.order_by(Task.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat()
        }
        for t in tasks
    ]


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: str,
    req: UpdateTaskStatusRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    task = db.query(Task).filter(
        Task.organization_id == org_id,
        Task.id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = req.status
    db.commit()
    db.refresh(task)
    return {"id": task.id, "status": task.status}
