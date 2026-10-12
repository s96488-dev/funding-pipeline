import logging
import time

from confluent_kafka import KafkaError, Message, Producer

from funding_pipeline.config import Settings
from funding_pipeline.ingestion.hyperliquid_client import fetch_snapshots
from funding_pipeline.models import AssetSnapshot

logger = logging.getLogger(__name__)


def create_producer(settings: Settings) -> Producer:

    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "acks": "all",
        "enable.idempotence": True,
    }
    return Producer(conf)


def _on_delivery(err: KafkaError | None, msg: Message) -> None:
    if err is not None:
        logger.error("Failed to deliver key=%r: %s", msg.key(), err)
    else:
        logger.debug(
            "Message saved in %s [partition %s] offset %s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


def publish_snapshots(
    producer: Producer, snapshots: list[AssetSnapshot], topic: str
) -> None:
    for snapshot in snapshots:
        producer.produce(
            topic,
            key=snapshot.coin_name.encode(),
            value=snapshot.model_dump_json().encode(),
            on_delivery=_on_delivery,
        )
    producer.flush()


def run(settings: Settings) -> None:
    producer = create_producer(settings)
    try:
        while True:
            started = time.monotonic()
            try:
                snapshots = fetch_snapshots()
                publish_snapshots(producer, snapshots, settings.snapshots_topic)
                logger.info(
                    "Published %s snapshots to %s",
                    len(snapshots),
                    settings.snapshots_topic,
                )
            except Exception:
                logger.exception("Failed to fetch or publish snapshots")

            gap = time.monotonic() - started
            sleep_for = max(0, settings.poll_interval_seconds - gap)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")
        producer.flush()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    run(settings)
