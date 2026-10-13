import logging

from confluent_kafka import Consumer, Message
from pydantic import ValidationError

from funding_pipeline.config import Settings
from funding_pipeline.models import AssetSnapshot
from funding_pipeline.processing.storage import create_db_engine, insert_snapshots

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
POLL_TIMEOUT_SECONDS = 1.0


def create_consumer(settings: Settings) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": settings.consumer_group_id,
            # A new group starts from the oldest message, so nothing is skipped.
            "auto.offset.reset": "earliest",
            # Offsets are committed manually, only after rows are in Postgres.
            "enable.auto.commit": False,
        }
    )


def parse_messages(messages: list[Message]) -> list[AssetSnapshot]:
    snapshots: list[AssetSnapshot] = []
    for msg in messages:
        if msg.error() is not None:
            logger.error("Kafka error: %s", msg.error())
            continue
        value = msg.value()
        if value is None:
            continue
        try:
            snapshots.append(AssetSnapshot.model_validate_json(value))
        except ValidationError:
            # A malformed message must not block the partition forever.
            logger.exception("Skipping invalid message at offset %s", msg.offset())
    return snapshots


def run(settings: Settings) -> None:
    consumer = create_consumer(settings)
    engine = create_db_engine(settings)
    consumer.subscribe([settings.snapshots_topic])
    try:
        while True:
            messages = consumer.consume(
                num_messages=BATCH_SIZE, timeout=POLL_TIMEOUT_SECONDS
            )
            if not messages:
                continue
            snapshots = parse_messages(messages)
            inserted = insert_snapshots(engine, snapshots)
            consumer.commit(asynchronous=False)
            logger.info(
                "Received %s snapshots, inserted %s new rows", len(snapshots), inserted
            )
    except KeyboardInterrupt:
        logger.info("Stopping consumer")
    finally:
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(Settings())
