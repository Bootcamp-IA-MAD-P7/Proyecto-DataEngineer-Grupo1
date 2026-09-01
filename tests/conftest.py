import os

SYNTHETIC_TEST_ENV = {
    "KAFKA_BOOTSTRAP_SERVERS": "synthetic-broker.invalid:9092",
    "KAFKA_CONSUMER_GROUP": "synthetic-group",
    "KAFKA_TOPICS": "synthetic-topic",
    "MONGODB_URI": "mongodb://synthetic-mongo.invalid:27017/synthetic",
    "MONGODB_DB": "synthetic_db",
    "MONGODB_COLLECTION": "synthetic_raw_events",
    "MONGODB_INVALID_COLLECTION": "synthetic_invalid_events",
}

for name, value in SYNTHETIC_TEST_ENV.items():
    os.environ.setdefault(name, value)

# Prevent test imports from reading the repository's local .env file. Tests that
# exercise python-dotenv explicitly re-enable it only for a synthetic temporary file.
os.environ.setdefault("PYTHON_DOTENV_DISABLED", "1")
