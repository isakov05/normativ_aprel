import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from tasks.models import Tasks

logger = logging.getLogger(__name__)


@shared_task
def log_task_created(task_id, title):
    logger.info(f'Background: Task #{task_id} created with title "{title}"')
    return f'Logged task #{task_id}'


@shared_task
def send_welcome_email(username):
    logger.info(f'Background: pretending to send a welcome email to {username}')
    return f'Email sent to {username}'


@shared_task
def check_old_tasks():
    threshold = timezone.now() - timedelta(days=7)
    old = Tasks.objects.filter(created_at__lt=threshold)
    count = old.count()
    logger.info(f'Periodic: found {count} task(s) older than 7 days')
    return count
