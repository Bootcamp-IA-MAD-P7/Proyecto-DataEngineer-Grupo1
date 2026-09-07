from __future__ import annotations


def mask_tail(value: str, keep: int = 3) -> str:
    clean = value.strip()
    if len(clean) <= keep:
        return "*" * len(clean)
    return "*" * (len(clean) - keep) + clean[-keep:]


def mask_passport(value: str) -> str:
    return mask_tail(value, 3)


def mask_phone(value: str) -> str:
    return mask_tail(value, 3)


def mask_email(value: str) -> str:
    parts = value.split("@")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return mask_tail(value, 2)
    local, domain = parts[0], parts[1]
    return f"{local[0]}***@{domain}"


def mask_ip(value: str) -> str:
    parts = value.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return f"{parts[0]}.{parts[1]}.x.x"
    return "*" * len(value)


def domain_completeness(person: dict[str, object]) -> int:  # noqa: C901
    count = 0
    if person.get("first_name") and person.get("last_name"):
        count += 1
    if person.get("email") or person.get("telephone_number"):
        count += 1
    locations = person.get("locations")
    if isinstance(locations, list) and len(locations) > 0:
        count += 1
    profiles = person.get("professional_profiles")
    if isinstance(profiles, list) and len(profiles) > 0:
        count += 1
    return count
