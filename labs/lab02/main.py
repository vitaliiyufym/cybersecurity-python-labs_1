"""Точка входу: команди demo та analyze."""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from labs.lab02 import task2
from labs.lab02.task1 import Admin, Session, User, UserAccount


def run_demo() -> None:
    print("=== 1. Створення користувача ===")
    user = User("alice", "alice_01@example.com", "user", "Secret123")
    account = UserAccount(user)
    print(user)

    print("\n=== 2. Невдалий і успішний вхід ===")
    print("Невірний пароль:", account.login("alice", "wrong", "192.168.1.10"))
    print("Вірний пароль:  ", account.login("alice", "Secret123", "192.168.1.10"))
    print("Автентифікований:", account.is_authenticated())

    print("\n=== 3. Зміна email з валідацією ===")
    user.email = "alice_new@example.com"
    print("Новий email:", user.email)
    try:
        user.email = "bad@x"
    except ValueError as e:
        print("Помилка:", e)

    print("\n=== 4. Права адміністратора ===")
    admin = Admin("root_admin", "root_admin@example.com", "AdminPass1")
    admin.grant_permission("read_logs")
    admin.grant_permission("manage_users")
    print(admin)
    print("read_logs:", admin.has_permission("read_logs"))
    admin.revoke_permission("read_logs")
    print("read_logs після відкликання:", admin.has_permission("read_logs"))

    print("\n=== 5. Доступ через account[...] ===")
    print("account['user'] ->", account["user"])
    try:
        account["password_hash"]
    except KeyError as e:
        print("KeyError:", e)
    try:
        account["user"] = "рядок"
    except TypeError as e:
        print("TypeError:", e)

    print("\n=== 6. Завершення сеансу за таймаутом ===")
    old = datetime.now(timezone.utc) - timedelta(minutes=20)
    account["session"] = Session("192.168.1.10", login_time=old)
    print("Автентифікований:", account.is_authenticated())

    print("\n=== 7. Вихід із системи ===")
    account.login("alice", "Secret123", "192.168.1.10")
    print("logout:", account.logout())
    print("Автентифікований:", account.is_authenticated())

    print("\n=== 8. Журнал аудиту ===")
    account.audit_log.show_all()


def run_analyze(args: argparse.Namespace) -> int:
    return task2.run(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ЛР №2")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="демонстрація Завдання 1")

    analyze = sub.add_parser("analyze", help="ARP-аудитор (варіант 11)")
    task2.add_arguments(analyze)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        sys.exit(run_analyze(args))


if __name__ == "__main__":
    main()
