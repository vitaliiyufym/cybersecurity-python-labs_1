"""Завдання 1: модель користувача, сесій та аудиту."""

import hashlib
import hmac
import ipaddress
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import ClassVar

PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 16  # байт
SESSION_TIMEOUT_SEC = 900
MIN_PASSWORD_LENGTH = 8

# Локальна частина: перша літера латинська, всього 3-64 символи [A-Za-z0-9_].
# Домен: мітки через крапку, мінімум одна крапка.
EMAIL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


class WeakPasswordError(ValueError):
    """Пароль не відповідає вимогам безпеки."""


class InvalidEmailError(ValueError):
    """Email не відповідає заданому формату."""


class InvalidIPError(ValueError):
    """Некоректна IP-адреса."""


def _require_text(value: object, name: str) -> str:
    """Повернути непорожній рядок або кинути TypeError / ValueError."""
    if not isinstance(value, str):
        raise TypeError(f"{name} має бути рядком, а не {type(value).__name__}")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} не може бути порожнім")
    return value


class User:
    """Користувач із безпечним зберіганням пароля."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        password: str,
        active: bool = True,
    ) -> None:
        self.username = _require_text(username, "username")
        self.email = email  # іде через setter з валідацією
        self.role = _require_text(role, "role")
        self.active = active
        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None
        self.set_password(password)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"email має бути рядком, а не {type(value).__name__}")
        if not EMAIL_PATTERN.fullmatch(value):
            raise InvalidEmailError(f"Некоректний email: {value!r}")
        self._email = value

    @staticmethod
    def _derive_hash(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)

    def set_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError("Пароль має бути рядком")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(
                f"Пароль закороткий: потрібно щонайменше {MIN_PASSWORD_LENGTH} символів"
            )
        self.__password_salt = os.urandom(SALT_SIZE)
        self.__password_hash = self._derive_hash(password, self.__password_salt)

    def check_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        if self.__password_hash is None or self.__password_salt is None:
            return False
        candidate = self._derive_hash(password, self.__password_salt)
        return hmac.compare_digest(candidate, self.__password_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "active" if self.active else "inactive"
        return (
            f"User(username={self.username}, email={self.email}, "
            f"role={self.role}, {status})"
        )


class Admin(User):
    """Адміністратор: користувач із набором дозволів."""

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        permissions: set[str] | None = None,
        active: bool = True,
    ) -> None:
        super().__init__(username, email, "admin", password, active)
        # нова множина для кожного об'єкта, а не спільна типова
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(_require_text(permission, "permission"))

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(_require_text(permission, "permission"))

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        perms = ", ".join(sorted(self.permissions)) or "none"
        return f"{super().__str__()} | permissions: {perms}"


class Session:
    """Сеанс користувача з відстеженням активності (час у UTC)."""

    def __init__(self, ip: str, login_time: datetime | None = None) -> None:
        if not isinstance(ip, str):
            raise TypeError("ip має бути рядком")
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise InvalidIPError(f"Некоректна IP-адреса: {ip!r}") from None
        if login_time is not None:
            if not isinstance(login_time, datetime):
                raise TypeError("login_time має бути datetime")
            if login_time.tzinfo is None:
                raise ValueError("login_time має містити часовий пояс (UTC)")
            if login_time > datetime.now(timezone.utc):
                raise ValueError("login_time не може бути в майбутньому")
        self.ip = ip
        self.login_time: datetime = login_time or datetime.now(timezone.utc)
        self.last_activity: datetime = self.login_time

    def touch(self) -> None:
        """Оновити час останньої активності."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Сеанс активний, якщо з останньої активності минуло менше timeout_sec."""
        if isinstance(timeout_sec, bool) or not isinstance(timeout_sec, int):
            raise TypeError("timeout_sec має бути цілим числом")
        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути додатним")
        idle = datetime.now(timezone.utc) - self.last_activity
        return idle < timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Один запис журналу аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал подій безпеки."""

    ALLOWED_ACTIONS = frozenset({"login_success", "login_failure", "logout"})

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        username = _require_text(username, "username")
        if action not in self.ALLOWED_ACTIONS:
            raise ValueError(f"Невідома дія: {action!r}")
        self.records.append(AuditRecord(datetime.now(timezone.utc), username, action))

    def show_all(self) -> None:
        if not self.records:
            print("Журнал порожній")
            return
        for r in self.records:
            print(f"{r.timestamp:%Y-%m-%d %H:%M:%S} UTC | {r.username} | {r.action}")


class UserAccount:
    """Композиція: User + Session + AuditLog."""

    # дозволені ключі -> (назва атрибута, допустимі типи)
    _KEYS: ClassVar[dict[str, tuple[str, tuple[type, ...]]]] = {
        "user": ("user", (User,)),
        "session": ("session", (Session, type(None))),
        "audit_log": ("audit_log", (AuditLog,)),
    }

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        if not isinstance(user, User):
            raise TypeError("user має бути об'єктом User")
        if session is not None and not isinstance(session, Session):
            raise TypeError("session має бути об'єктом Session або None")
        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise TypeError("audit_log має бути об'єктом AuditLog або None")
        self.user = user
        self.session = session
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        ok = (
            self.user.active
            and username == self.user.username
            and self.user.check_password(password)
        )
        if not ok:
            self.audit_log.add_log(username, "login_failure")
            return False
        try:
            new_session = Session(ip)  # сеанс створюється лише після успіху
        except (TypeError, InvalidIPError):
            self.audit_log.add_log(username, "login_failure")
            raise
        new_session.touch()
        self.session = new_session
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False
        if not self.session.is_active(SESSION_TIMEOUT_SEC):
            return False  # прострочений сеанс не подовжуємо
        self.session.touch()
        return True

    def logout(self) -> bool:
        if self.session is None:
            return False
        self.audit_log.add_log(self.user.username, "logout")
        self.session = None
        return True

    def __getitem__(self, key: str):
        if key not in self._KEYS:
            raise KeyError(key)
        return getattr(self, self._KEYS[key][0])

    def __setitem__(self, key: str, value) -> None:
        if key not in self._KEYS:
            raise KeyError(key)
        attr, types = self._KEYS[key]
        if not isinstance(value, types):
            raise TypeError(f"Для ключа {key!r} очікується {types}, а не {type(value)}")
        setattr(self, attr, value)