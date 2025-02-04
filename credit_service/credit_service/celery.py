from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_service.settings')
app = Celery('credit_service')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'initiate-billing-every-day': {
        'task': 'api.tasks.process_billing',
        'schedule': crontab(hour=0, minute=0),  # Runs daily at midnight
    },
}