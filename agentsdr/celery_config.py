"""
Celery Configuration
InboxAI - Lindy AI-like Email Automation Platform
"""

import os
from celery import Celery
from celery.schedules import crontab

# Initialize Celery
celery_app = Celery(
    'inboxai',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'agentsdr.email.tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer=os.getenv('CELERY_TASK_SERIALIZER', 'json'),
    result_serializer=os.getenv('CELERY_RESULT_SERIALIZER', 'json'),
    accept_content=[os.getenv('CELERY_ACCEPT_CONTENT', 'json')],
    timezone=os.getenv('CELERY_TIMEZONE', 'UTC'),
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    'fetch-emails-every-5-minutes': {
        'task': 'agentsdr.email.tasks.fetch_all_user_emails',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'process-scheduled-follow-ups': {
        'task': 'agentsdr.email.tasks.process_follow_ups',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'reset-monthly-credits': {
        'task': 'agentsdr.email.tasks.reset_monthly_credits',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),  # First day of month
    },
}

if __name__ == '__main__':
    celery_app.start()
