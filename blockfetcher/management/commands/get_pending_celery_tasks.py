from ethstakersclub.celery import app as celery_app
import base64
import json
from django.core.management.base import BaseCommand


def get_scheduled_tasks_count(queue_name="celery"):
    with celery_app.pool.acquire(block=True) as conn:
        tasks = conn.default_channel.client.lrange(queue_name, 0, -1)
        decoded_tasks = []

    for task in tasks:
        j = json.loads(task)
        body = json.loads(base64.b64decode(j['body']))
        decoded_tasks.append(body)

    return len(decoded_tasks)


def get_celery_queue_len(queue_name):
    from ethstakersclub.celery import app as celery_app
    with celery_app.pool.acquire(block=True) as conn:
        return conn.default_channel.client.llen(queue_name)


def get_celery_queue_items(queue_name):
    import base64
    import json
    from ethstakersclub.celery import app as celery_app

    with celery_app.pool.acquire(block=True) as conn:
        tasks = conn.default_channel.client.lrange(queue_name, 0, -1)

    decoded_tasks = []

    for task in tasks:
        j = json.loads(task)
        body = json.loads(base64.b64decode(j['body']))
        decoded_tasks.append(body)

    return decoded_tasks


class Command(BaseCommand):
    help = 'Prints the pending celery tasks'

    def handle(self, *args, **options):
        print(get_celery_queue_items("celery"))
        print(get_scheduled_tasks_count())
