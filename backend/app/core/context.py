import contextvars
from typing import Optional

# Thread-safe / async-safe ContextVar to hold current organization ID
_tenant_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(org_id: Optional[str]) -> contextvars.Token:
    """Sets the active organization ID for the current async execution context."""
    return _tenant_context.set(org_id)


def get_current_tenant_id() -> Optional[str]:
    """Retrieves the active organization ID for the current context."""
    return _tenant_context.get()


def reset_current_tenant_id(token: contextvars.Token) -> None:
    """Resets the context back to its previous state."""
    _tenant_context.reset(token)
