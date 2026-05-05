"""Auth glue.

Local dev: AUTH_DISABLED=true bypasses entirely. Set false to exercise a
single hard-coded demo user.

Production: replace `_verify_demo_credentials` with a Cognito call. The
shape of the user object (id, email, groups) is what `current_user` exposes
downstream, so swap the verifier without touching the rest of the app.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from flask import session
from flask_login import LoginManager, UserMixin, login_user, logout_user

from app.config import Config


@dataclass
class User(UserMixin):
    id: str
    email: str
    groups: tuple[str, ...] = ()


_DEMO_USERS = {
    "demo@example.com": ("demo", "analyst"),
    "admin@example.com": ("admin", "admin"),
}


def _verify_demo_credentials(email: str, password: str) -> Optional[User]:
    if password != "demo" or email not in _DEMO_USERS:
        return None
    uid, role = _DEMO_USERS[email]
    return User(id=uid, email=email, groups=(role,))


def init_auth(server) -> LoginManager:
    lm = LoginManager()
    lm.login_view = "/login"
    lm.init_app(server)

    @lm.user_loader
    def _load(user_id: str) -> Optional[User]:
        if Config.AUTH_DISABLED:
            return User(id="local", email="local@dev", groups=("admin",))
        email = session.get("email")
        if not email:
            return None
        match = next((u for u, (uid, _) in _DEMO_USERS.items() if uid == user_id), None)
        if not match:
            return None
        _, role = _DEMO_USERS[match]
        return User(id=user_id, email=match, groups=(role,))

    return lm


def attempt_login(email: str, password: str) -> bool:
    user = _verify_demo_credentials(email, password)
    if not user:
        return False
    session["email"] = user.email
    login_user(user)
    return True


def do_logout() -> None:
    session.pop("email", None)
    logout_user()
