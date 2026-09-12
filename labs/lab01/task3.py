import csv
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

SALT = "00011"


class ValidationError(Exception):
    pass


def generate_hash(password, salt="00000"):
    if password == None or password == "" or salt == None or salt == "":
        raise ValueError("Пароль чи сіль не можуть бути порожніми")

    if len(password) < 12:
        raise ValidationError("Пароль повинен бути не менше 12 символів")

    combined = password + salt
    hash_object = hashlib.blake2b(combined.encode())
    return hash_object.hexdigest()


users_to_register = (
    ("alice_92", "SecurePass123!"),
    ("bob_smith", "MyStr0ngPass!"),
    ("carol_j", "P@ssword12345"),
    ("dave_k", "Qwerty!2023456"),
    ("emma_w", "Complex#Pass99"),
    ("frank_m", "Secret!Key1234"),
    ("grace_l", "Hidden$Value22"),
    ("henry_p", "Access!Code789"),
    ("irene_r", "Login#Test4567"),
    ("jack_t", "Final!Pass9999"),
)


def create_user(username, password):
    hash_value = generate_hash(password, SALT)
    return (username, hash_value)


def create_users(users_list):
    os.makedirs("labs/lab01/data", exist_ok=True)
    with open("labs/lab01/data/users.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for username, password in users_list:
            username, hash_value = create_user(username, password)
            writer.writerow([username, hash_value])


def read_users():
    with open("labs/lab01/data/users.csv", "r") as file:
        reader = csv.reader(file)
        return list(reader)


def log_event(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            status = "success" if result else "failure"
        except Exception:  # noqa: BLE001
            result = False
            status = "failure"

        log_entry = {
            "event": "login",
            "user": args[0] if args else "unknown",
            "result": status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # noqa: DTZ005
            "args": list(args),
            "kwargs": kwargs,
        }

        os.makedirs("labs/lab01/data", exist_ok=True)
        log_file = "labs/lab01/data/log.json"

        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_entry)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)

        return result

    return wrapper


@log_event
def login(username, password):
    if username == "" or username is None or password == "" or password is None:
        raise ValueError("Логін чи пароль не можуть бути порожніми")

    users_db = read_users()
    for row in users_db:
        db_username, db_hash = row[0], row[1]
        if db_username == username:
            input_hash = generate_hash(password, SALT)
            return input_hash == db_hash

    return False


def main():
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print()

    try:
        create_users(users_to_register)
        print("Користувачів успішно зареєстровано.\n")

        users_db = read_users()
        print(f"{'Логін':<15} {'Хеш пароля':<20}")
        for row in users_db:
            print(f"{row[0]:<15} {row[1]:<20}")
        print()

        print("Тест автентифікації:")
        print("alice_92 з правильним паролем:", login("alice_92", "SecurePass123!"))
        print("alice_92 з неправильним паролем:", login("alice_92", "WrongPassword123"))

    except FileNotFoundError:
        print("Помилка: файл не знайдено.")
    except PermissionError:
        print("Помилка: немає прав доступу до файлу.")
    except OSError:
        print("Помилка вводу/виводу.")
    except ValidationError as e:
        print(f"Помилка валідації: {e}")
    except ValueError as e:
        print(f"Помилка значення: {e}")


if __name__ == "__main__":
    main()
