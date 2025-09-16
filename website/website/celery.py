import os

from celery import Celery
from django.apps import apps

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

app = Celery('website')

# Configure Celery using settings from Django settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs.
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
