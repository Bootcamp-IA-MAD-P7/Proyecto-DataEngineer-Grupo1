from .error_handler import get_logger

logger = get_logger("validator")

REQUIRED_FIELDS: dict[str, list[str]] = {
    "net-data":          ["IPv4"],
    "bank-data":         ["IBAN", "salary"],
    "professional-data": ["company", "job"],
    "location":          ["fullname", "city"],
    "personal-data":     ["name", "last_name", "passport", "email"],
}


def validate(topic: str, data: dict[str, object]) -> bool:
    if topic not in REQUIRED_FIELDS:
        logger.warning("Unknown topic: %s", topic)
        return False
    if not isinstance(data, dict):
        logger.warning("Data is not a dict | topic=%s", topic)
        return False
    present = [f for f in REQUIRED_FIELDS[topic] if data.get(f)]
    if not present:
        logger.warning(
            "No identifying fields found %s | topic=%s",
            REQUIRED_FIELDS[topic],
            topic,
        )
        return False
    return True
