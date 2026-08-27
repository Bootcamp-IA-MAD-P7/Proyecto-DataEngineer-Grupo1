import json
from confluent_kafka import Consumer, KafkaError

c = Consumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "explorer-tmp",
        "auto.offset.reset": "earliest",
    }
)

c.subscribe(
    [
        "personal-data",
        "location",
        "professional-data",
        "bank-data",
        "net-data",
    ]
)

print("Reading messages... Ctrl+C to stop\n")

try:
    count = 0
    while count < 30:
        msg = c.poll(timeout=5.0)

        if msg is None:
            print("No message in 5 seconds — is Kafka running?")
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f"End of partition: {msg.topic()} [{msg.partition()}]")
            else:
                print(f"Error: {msg.error()}")
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
