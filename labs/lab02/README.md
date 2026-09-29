# Лабораторна робота №2. Консольні утиліти для кібербезпеки

**Варіант 11:** Аудитор ARP-таблиць та виявлення ARP-Spoofing.

## Встановлення

З кореня репозиторію, з активованим `.venv`:

```powershell
pip install -r requirements.txt
```

## Структура файлів

```
labs/lab02/
├── __init__.py
├── main.py      # команди demo та analyze
├── task1.py     # ООП: User, Admin, Session, AuditLog, UserAccount
├── task2.py     # ARP-аудитор (варіант 11)
├── README.md
└── data/
    └── data_v11/
        └── arp_table.csv   # вхідний файл (IP Address, MAC Address, Interface, Type)
```

## Запуск

Усі команди виконуються з кореня репозиторію.

Завдання 1 (демонстрація):

```powershell
python -m labs.lab02.main demo
```

Завдання 2 (ARP-аудитор):

```powershell
python -m labs.lab02.main analyze --arp-file labs/lab02/data/data_v11/arp_table.csv --detect-spoofing --output-json labs/lab02/data/arp_security_alerts.json --log-file labs/lab02/data/arp_audit.log
```

## Параметри CLI (analyze)

| Параметр | Обов'язковий | Опис |
|---|---|---|
| `--arp-file` | так | шлях до CSV з ARP-таблицею |
| `--output-json` | ні | шлях до JSON-звіту |
| `--detect-spoofing` | ні | прапорець: шукати один MAC для різних IP |
| `--log-file` | ні | файл журналу подій |

## Що робить утиліта

1. Читає CSV (`csv.DictReader`) і перевіряє наявність колонок.
2. Перевіряє IPv4 та MAC регулярними виразами (`re`); MAC приймається у форматі `XX:XX:XX:XX:XX:XX` або `XX-XX-XX-XX-XX-XX`.
3. З параметром `--detect-spoofing` групує записи за MAC (`collections.defaultdict`) і знаходить MAC, пов'язані з кількома IP.
4. Конфлікти зберігаються в `@dataclass SpoofingConflict`.
5. Події пишуться через `logging` (`WARNING` для некоректних записів, `CRITICAL` для spoofing); звіт експортується в JSON.

## Поведінка при помилках

- Файл не знайдено: `[ERROR] Файл не знайдено`, код завершення 1.
- Немає потрібних колонок або файл пошкоджений: `[ERROR] Не вдалося прочитати файл`, код 1.
- Не вдалося записати звіт: `[ERROR]`, код 1.
- Некоректні IP/MAC не зупиняють роботу: вони фіксуються у виводі й журналі.

## Результати на даних варіанта

- Усього записів: 11; коректних: 8; некоректних: 3.
- Некоректні: рядок 10 (IP `999.168.1.30`), рядок 11 (MAC `GG:11:22:33:44:55`), рядок 12 (MAC у форматі `0011.2233.4455`).
- Виявлено ARP-spoofing: MAC `DE:AD:BE:EF:00:01` пов'язаний з `192.168.1.20`, `192.168.1.21`, `192.168.1.22`.

## Перевірка коду

```powershell
ruff check .
ruff format --check .
```