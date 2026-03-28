import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from redis import Redis
from redis.exceptions import ResponseError

from moderation_api.queue import enqueue_from_event, parse_event


class Command(BaseCommand):
    help = "Consume B2B product events from Redis Stream and enqueue moderation cards"

    def handle(self, *args, **options):
        stream = settings.MODERATION_EVENTS_STREAM
        group = settings.MODERATION_EVENTS_GROUP
        consumer = settings.MODERATION_EVENTS_CONSUMER

        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)

        self._ensure_group(redis_client, stream, group)
        self.stdout.write(self.style.SUCCESS(f"Listening stream={stream} group={group} consumer={consumer}"))

        while True:
            entries = redis_client.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={stream: ">"},
                count=20,
                block=5000,
            )
            if not entries:
                continue

            for _stream_name, messages in entries:
                for message_id, fields in messages:
                    try:
                        event = parse_event(fields)
                        card = enqueue_from_event(event)
                        redis_client.xack(stream, group, message_id)
                        if card:
                            self.stdout.write(f"[{message_id.decode('utf-8')}] queued product={card.product_id}")
                        else:
                            self.stdout.write(self.style.WARNING(f"[{message_id.decode('utf-8')}] skipped invalid event"))
                    except Exception as exc:  # noqa: BLE001
                        connection.close_if_unusable_or_obsolete()
                        self.stderr.write(self.style.ERROR(f"[{message_id.decode('utf-8')}] failed: {exc}"))
                        time.sleep(0.2)

    def _ensure_group(self, redis_client, stream, group):
        try:
            redis_client.xgroup_create(name=stream, groupname=group, id="$", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
