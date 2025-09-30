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
    include=['backend.tasks']  # Module where tasks are defined
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
        'task': 'backend.tasks.run_daily_billing_jobs',
        'schedule': crontab(hour=2, minute=0),
    },
    'collect-snmp-data': {
        'task': 'backend.tasks.collect_snmp_data',
        'schedule': crontab(minute='*/5'),
    },
    'collect-performance-data': {
        'task': 'backend.tasks.collect_performance_data',
        'schedule': crontab(minute='*/5'),
    },
    'detect-network-incidents': {
        'task': 'backend.tasks.detect_network_incidents',
        'schedule': crontab(minute='*/10'),
    },
    'auto-resolve-incidents': {
        'task': 'backend.tasks.auto_resolve_incidents',
        'schedule': crontab(minute='*/15'),
    },
    'escalate-incidents': {
        'task': 'backend.tasks.escalate_incidents',
        'schedule': crontab(minute='*/30'),
    },
    'refresh-topology-status': {
        'task': 'backend.tasks.refresh_topology_status',
        'schedule': crontab(minute='*/10'),
    },
    'generate-network-analytics': {
        'task': 'backend.tasks.generate_network_analytics',
        'schedule': crontab(hour=3, minute=0),
    },
    'cleanup-old-monitoring-data': {
        'task': 'backend.tasks.cleanup_old_monitoring_data',
        'schedule': crontab(day_of_week='sunday', hour=4, minute=0),
    },
}

if __name__ == '__main__':
    app.start()