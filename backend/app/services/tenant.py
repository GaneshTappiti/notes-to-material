"""Tenant scoping utilities.

Provides a dependency + decorator to enforce tenant_id filtering automatically
on DB queries. For now, tenant id is derived from header X-Tenant or current_user.
If absent, acts in single-tenant mode unless SINGLE_TENANT=1.
"""
from __future__ import annotations
from fastapi import Header, HTTPException, Depends
from typing import Callable, TypeVar, ParamSpec
from .auth import current_user, User  # type: ignore
from functools import wraps

TenantId = str | None
P = ParamSpec('P')
R = TypeVar('R')

def tenant_id(x_tenant: str | None = Header(default=None), user: User = Depends(current_user)) -> str | None:  # pragma: no cover
    return x_tenant or getattr(user, 'tenant_id', None)

def enforce_tenant(fn: Callable[P, R]) -> Callable[P, R]:
    """Decorator that ensures tenant_id kwarg is provided in multi-tenant mode.

    Set SINGLE_TENANT=1 to disable enforcement.
    """
    import os, inspect
    sig = inspect.signature(fn)
    single = os.getenv('SINGLE_TENANT','0') == '1'
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if 'tenant_id' in sig.parameters and kwargs.get('tenant_id') is None and not single:
            raise HTTPException(status_code=400, detail='tenant_id required')
        return fn(*args, **kwargs)
    return wrapper

__all__ = ['tenant_id','enforce_tenant']
