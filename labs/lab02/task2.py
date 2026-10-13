"""Завдання 2 (варіант 11): аудитор ARP-таблиць та виявлення ARP-spoofing."""

import argparse
import csv
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("arp_audit")


class ArpFileError(Exception):
    """Файл ARP-таблиці порожній, пошкоджений або має неправильну структуру."""


REQUIRED_COLUMNS = ("IP Address", "MAC Address", "Interface", "Type")

# IPv4: чотири октети 0-255 (без ведучих нулів, окрім самого 0).
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4_PATTERN = re.compile(rf"^{_OCTET}(?:\.{_OCTET}){{3}}$")
# MAC: шість пар hex-цифр, розділених ':' або '-' (один тип розділювача).
MAC_PATTERN = re.compile(
    r"^(?:[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}|[0-9A-Fa-f]{2}(?:-[0-9A-Fa-f]{2}){5})$"
)


@dataclass
class ArpEntry:
    """Один рядок ARP-таблиці."""

    line: int
    ip: str
    mac: str
    interface: str
    entry_type: str
    valid_ip: bool = True
    valid_mac: bool = True

    @property
    def is_valid(self) -> bool:
        return self.valid_ip and self.valid_mac


@dataclass
class SpoofingConflict:
    """Одна MAC-адреса, пов'язана з кількома IP (ознака ARP-spoofing/MITM)."""

    mac: str
    ips: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)


def normalize_mac(mac: str) -> str:
    """Привести MAC до верхнього регістру з двокрапками."""
    return mac.replace("-", ":").upper()


def read_arp_table(path: Path) -> list[ArpEntry]:
    """Прочитати CSV і перевірити IP та MAC кожного запису."""
    entries: list[ArpEntry] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ArpFileError("файл порожній")
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ArpFileError(f"бракує колонок: {', '.join(missing)}")
        for row in reader:
            if None in row:  # у рядку більше полів, ніж у заголовку
                logger.warning("Рядок %d: зайві поля, рядок пропущено", reader.line_num)
                continue
            ip = (row["IP Address"] or "").strip()
            mac = (row["MAC Address"] or "").strip()
            entries.append(
                ArpEntry(
                    line=reader.line_num,
                    ip=ip,
                    mac=mac,
                    interface=(row["Interface"] or "").strip(),
                    entry_type=(row["Type"] or "").strip(),
                    valid_ip=bool(IPV4_PATTERN.fullmatch(ip)),
                    valid_mac=bool(MAC_PATTERN.fullmatch(mac)),
                )
            )
    if not entries:
        raise ArpFileError("файл не містить жодного запису")
    return entries


def find_spoofing(entries: list[ArpEntry]) -> list[SpoofingConflict]:
    """Знайти MAC-адреси, що відповідають кільком різним IP."""
    by_mac: dict[str, list[ArpEntry]] = defaultdict(list)
    for e in entries:
        if e.is_valid:
            by_mac[normalize_mac(e.mac)].append(e)

    conflicts = []
    for mac, group in by_mac.items():
        ips = sorted({e.ip for e in group})
        if len(ips) > 1:
            interfaces = sorted({e.interface for e in group})
            conflicts.append(SpoofingConflict(mac, ips, interfaces))
    return sorted(conflicts, key=lambda c: c.mac)


def setup_logging(log_file: Path | None) -> None:
    """Логування: у консоль (INFO) і, за потреби, у файл."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )


def json_path(value: str) -> Path:
    """Тип для argparse: шлях має закінчуватися на .json."""
    path = Path(value)
    if path.suffix.lower() != ".json":
        raise argparse.ArgumentTypeError(f"очікується файл .json, а не {value!r}")
    return path


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--arp-file", type=Path, required=True, help="CSV з ARP-таблицею"
    )
    parser.add_argument("--output-json", type=json_path, help="шлях до JSON-звіту")
    parser.add_argument(
        "--detect-spoofing",
        action="store_true",
        help="шукати дублікати MAC для різних IP",
    )
    parser.add_argument("--log-file", type=Path, help="файл журналу подій")


def run(args: argparse.Namespace) -> int:
    """Виконати аналіз. Повертає код завершення (0 - успіх, 1 - помилка)."""
    if args.output_json and args.output_json.resolve() == args.arp_file.resolve():
        print("[ERROR] --output-json не може збігатися з вхідним файлом")
        return 1
    try:
        setup_logging(args.log_file)
    except OSError as exc:
        print(f"[ERROR] Не вдалося відкрити файл журналу: {exc}")
        return 1
    try:
        logger.info("Parsing ARP table snapshot from %s...", args.arp_file)
        entries = read_arp_table(args.arp_file)
    except FileNotFoundError:
        logger.error("Файл не знайдено: %s", args.arp_file)
        return 1
    except IsADirectoryError:
        logger.error("Вказано папку, а не файл: %s", args.arp_file)
        return 1
    except PermissionError:
        logger.error("Немає прав на читання файлу: %s", args.arp_file)
        return 1
    except ArpFileError as exc:
        logger.error("Некоректний файл ARP-таблиці: %s", exc)
        return 1
    except UnicodeDecodeError:
        logger.error("Файл має не UTF-8 кодування: %s", args.arp_file)
        return 1
    except (csv.Error, OSError) as exc:
        logger.error("Не вдалося прочитати файл: %s", exc)
        return 1

    valid = [e for e in entries if e.is_valid]
    invalid = [e for e in entries if not e.is_valid]
    logger.info("Validated %d IP/MAC entries.", len(entries))

    print("\n=== Validated Entries Summary ===")
    print(f"Valid IP/MAC Pairs : {len(valid)}")
    print(f"Invalid Syntax     : {len(invalid)}")
    for e in invalid:
        reasons = []
        if not e.valid_ip:
            reasons.append(f"IP {e.ip!r}")
        if not e.valid_mac:
            reasons.append(f"MAC {e.mac!r}")
        logger.warning("Рядок %d: некоректний %s", e.line, ", ".join(reasons))
        print(f"  [INVALID] line {e.line}: {', '.join(reasons)}")

    conflicts: list[SpoofingConflict] = []
    if args.detect_spoofing:
        conflicts = find_spoofing(entries)
        if conflicts:
            print("\n=== CRITICAL SECURITY ALERTS: ARP-SPOOFING DETECTED ===")
        else:
            print("\nARP-spoofing не виявлено.")
        for c in conflicts:
            print("[ALERT] MAC Address Duplicate Conflict!")
            print(f"MAC Address: {c.mac} associated with MULTIPLE IP addresses:")
            for ip in c.ips:
                print(f"- {ip}")
            print("-> POSSIBLE MAN-IN-THE-MIDDLE / ARP-SPOOFING ATTACK!")
            logger.critical(
                "ARP-spoofing: MAC %s -> IPs %s (interfaces: %s)",
                c.mac,
                ", ".join(c.ips),
                ", ".join(c.interfaces),
            )

    if args.output_json:
        report = {
            "source_file": str(args.arp_file),
            "total_entries": len(entries),
            "valid_entries": len(valid),
            "invalid_entries": [asdict(e) for e in invalid],
            "spoofing_checked": args.detect_spoofing,
            "spoofing_conflicts": [asdict(c) for c in conflicts],
        }
        try:
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Не вдалося записати звіт: %s", exc)
            return 1
        logger.info("Critical conflict logged to %s", args.output_json)
    return 0