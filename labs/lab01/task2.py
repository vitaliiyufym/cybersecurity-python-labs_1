import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
users = {
    "risk_manager": {
        "role": "risk_analyst",
        "clearance": 4,
        "department": "Risk Management",
        "active": True,
    },
    "business_analyst": {
        "role": "business_analyst",
        "clearance": 2,
        "department": "Business",
        "active": True,
    },
    "legal_counsel": {
        "role": "legal",
        "clearance": 3,
        "department": "Legal",
        "active": True,
    },
    "contractor_dev": {
        "role": "contractor",
        "clearance": 2,
        "department": "Contract",
        "active": True,
    },
    "obsolete_system": {
        "role": "legacy_system",
        "clearance": 1,
        "department": "Legacy",
        "active": False,
    },
}

resources = [
    ("risk_registers", 4),
    ("business_requirements", 2),
    ("legal_documents", 3),
    ("contract_code", 2),
    ("governance_framework", 4),
    ("meeting_minutes", 1),
    ("regulatory_reports", 3),
    ("executive_dashboards", 4),
    ("project_specs", 2),
    ("public_statements", 1),
]

security_levels = ("Public", "Internal Use", "Restricted", "Highly Restricted")

blocked_users = {"obsolete_system", "contract_expired", "legal_hold"}
for name, level in resources:
    level_name = security_levels[level - 1]
    print(f"{name} -> {level_name}")


def check_access(username, resource_name, resource_level):
    if username not in users:
        return "DENY (User not found)"

    if username in blocked_users:
        return "DENY (User is blocked)"

    if users[username]["active"] == False:
        return "DENY (Account inactive)"

    if users[username]["clearance"] >= resource_level:
        return "ALLOW"
    else:
        return "DENY (Insufficient clearance)"


for username in users:
    for name, level in resources:
        result = check_access(username, name, level)
        print(f"user={username} resource={name} -> {result}")
