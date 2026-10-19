from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.entities import Membership, Organization, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterTenantRequest(BaseModel):
    company_name: str
    company_slug: str
    admin_name: str
    admin_email: str
    password: str


@router.post("/register")
def register_tenant(req: RegisterTenantRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Self-serve tenant and organization registration."""
    existing_org = db.query(Organization).filter(Organization.slug == req.company_slug).first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Company slug already taken")

    existing_user = db.query(User).filter(User.email == req.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=req.company_name, slug=req.company_slug)
    db.add(org)
    db.flush()

    user = User(
        email=req.admin_email,
        hashed_password=hash_password(req.password),
        full_name=req.admin_name,
        is_active=True,
        is_platform_admin=False
    )
    db.add(user)
    db.flush()

    membership = Membership(
        organization_id=org.id,
        user_id=user.id,
        role="tenant_admin"
    )
    db.add(membership)
    db.commit()

    token = create_access_token({"sub": user.id, "organization_id": org.id, "role": "tenant_admin"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "organization": {"id": org.id, "name": org.name, "slug": org.slug},
        "user": {"id": user.id, "email": user.email, "name": user.full_name, "role": "tenant_admin"}
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """User authentication returning JWT with embedded tenant claims."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    org_id = membership.organization_id if membership else None
    role = membership.role if membership else ("platform_admin" if user.is_platform_admin else "viewer")

    token = create_access_token({"sub": user.id, "organization_id": org_id, "role": role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": role,
            "organization_id": org_id
        }
    }
