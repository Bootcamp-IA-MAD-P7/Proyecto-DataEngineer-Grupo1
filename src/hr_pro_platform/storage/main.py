from __future__ import annotations

from .postgres import PostgresSchemaClient


def main() -> None:
    client = PostgresSchemaClient()
    try:
        client.connect()
        client.create_schema()
    finally:
        client.close()


if __name__ == "__main__":
    main()
