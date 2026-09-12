import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

passwords = [
    "APT@Detect10n",
    "simple",
    "Red@Team2023",
    "participant",
    "Blue@T3am",
    "common123",
    "Purple@T34m",
    "regular123",
    "Gr33n@Team",
    "normal123",
]

criteria = {
    "min_length": 7,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "simple",
    "participant",
    "common123",
    "regular123",
    "normal123",
    "test",
}


def check_criteria(password):
    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_special = any(not char.isalnum() for char in password)
    return has_digit, has_upper, has_special


def evaluate_password(password, all_passwords):
    has_digit, has_upper, has_special = check_criteria(password)
    has_lower = any(char.islower() for char in password)
    length_ok = len(password) >= criteria["min_length"]
    very_strong_length = len(password) >= criteria["min_length"] + 4
    is_unique = all_passwords.count(password) == 1

    if password in forbidden_passwords or not length_ok:
        return "Заборонений"

    all_criteria_met = has_digit and has_upper and has_special and length_ok

    if all_criteria_met and very_strong_length and is_unique:
        return "Дуже сильний"

    if all_criteria_met:
        return "Сильний"

    criteria_count = sum([has_digit, has_upper, has_special, has_lower])

    if length_ok and 0 < criteria_count < 4:
        return "Середній"

    return "Слабкий"


random_indices = random.sample(range(len(passwords)), 3)

for index in random_indices:
    passwords.append(passwords[index])

print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
print()

print(f"{'Пароль':<20} {'Категорія':<20}")
print("-" * 40)

for password in passwords:
    category = evaluate_password(password, passwords)
    print(f"{password:<20} {category:<20}")
