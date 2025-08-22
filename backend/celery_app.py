import os
from celery import Celery
from celery.schedules import crontab

# Celery configuration
# Ensure you have a Redis server running.
# You can set these URLs in your environment variables.
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Initialize Celery
app = Celery(
    'isp_project_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']  # Module where tasks are defined
)

# Optional configuration
app.conf.update(
    result_expires=3600,
    timezone='UTC', # It's good practice to use UTC for scheduling
)

# Celery Beat (Scheduler) configuration
app.conf.beat_schedule = {
    # Executes daily at 2:00 AM UTC.
    'run-daily-billing-jobs': {
        'task': 'tasks.run_daily_billing_jobs',
        'schedule': crontab(hour=2, minute=0),
    },
}

if __name__ == '__main__':
    app.start()