def detect_topic(data: dict[str, object]) -> str | None:
    keys = set(data.keys())

    if "IBAN" in keys or "salary" in keys:
        return "bank-data"

    if (
        "company" in keys
        or "company address" in keys
        or "company_telfnumber" in keys
        or "company_email" in keys
        or "job" in keys
    ):
        return "professional-data"

    if "city" in keys:
        return "location"

    if (
        "name" in keys
        or "last_name" in keys
        or "sex" in keys
        or "telfnumber" in keys
        or "email" in keys
    ):
        return "personal-data"

    if "IPv4" in keys:
        return "net-data"

    return None
