from typing import Optional
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.context import get_current_tenant_id, set_current_tenant_id
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.entities import Membership, Organization, User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None)
) -> User:
    """Authenticates the user via Bearer JWT and sets the active organization scope."""
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(auth.credentials)
    if not claims or "sub" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == claims["sub"], User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    # Resolve organization context
    org_id = x_organization_id or claims.get("organization_id")
    if not org_id and not user.is_platform_admin:
        membership = db.query(Membership).filter(Membership.user_id == user.id).first()
        if membership:
            org_id = membership.organization_id

    if org_id:
        request.state.tenant_id = org_id
        set_current_tenant_id(org_id)

    return user


async def get_current_tenant(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """Returns the validated active organization ID for the authenticated user."""
    org_id = getattr(request.state, "tenant_id", None) or get_current_tenant_id()
    if not org_id and not user.is_platform_admin:
        # Fallback to query
        membership = db.query(Membership).filter(Membership.user_id == user.id).first()
        if membership:
            org_id = membership.organization_id

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active organization context found for this request"
        )

    # Verify membership unless platform admin
    if not user.is_platform_admin:
        membership = db.query(Membership).filter(
            Membership.user_id == user.id,
            Membership.organization_id == org_id
        ).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

    return org_id
