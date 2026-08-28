import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confluent_kafka import Consumer, KafkaError

from hr_pro_platform.ingestion.config import KAFKA_CONFIG

explorer_config = {**KAFKA_CONFIG, "group.id": "explorer-tmp"}

c = Consumer(explorer_config)
c.subscribe(["probando"])

print("Reading 30 messages...\n")

try:
    count = 0
    while count < 30:
        msg = c.poll(timeout=5.0)

        if msg is None:
            print("No message in 5 seconds — is Kafka running?")
            continue

        if msg.error():
            error = msg.error()
            if error.code() == KafkaError._PARTITION_EOF:
                print(f"End of partition: {msg.topic()} [{msg.partition()}]")
            else:
                print(f"Error: {error}")
            continue

        data = json.loads(msg.value().decode("utf-8"))

        print(f"TOPIC:     {msg.topic()}")
        print(f"PARTITION: {msg.partition()}")
        print(f"OFFSET:    {msg.offset()}")
        print(f"DATA:      {json.dumps(data, indent=2)}")
        print("---")

        count += 1

finally:
    c.close()
    print("Done.")
