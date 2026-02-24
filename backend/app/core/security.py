from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings


@dataclass
class UserContext:
    username: str
    role: str


def require_user(
    x_user: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> UserContext:
    settings = get_settings()
    allowed_roles = {r.strip() for r in settings.allowed_roles.split(",") if r.strip()}

    if not x_user or not x_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User or X-Role headers",
        )

    if x_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not allowed")

    return UserContext(username=x_user, role=x_role)


def require_reviewer(user: UserContext = Depends(require_user)) -> UserContext:
    if user.role not in {"Reviewer", "Admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or Admin role required",
        )
    return user
