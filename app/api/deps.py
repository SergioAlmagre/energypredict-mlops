from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.models import User
from app.db.session import get_db


def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user_dep(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_roles_dep(*roles: str) -> Callable[[User], User]:
    role_dep = require_roles(*roles)

    def dependency(current_user: User = Depends(role_dep)) -> User:
        return current_user

    return dependency
