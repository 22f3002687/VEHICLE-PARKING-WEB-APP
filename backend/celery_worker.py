from backend.app import create_app
from celery.schedules import crontab

# Create a Flask app instance. This will also configure Celery.
flask_app = create_app()

# Import the celery instance from the extensions file.
from backend.extensions import celery

# --- Celery Beat Schedule ---
# This configuration must be done on the final celery object
celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'backend.tasks.send_daily_reminders',
        'schedule': crontab(hour=19, minute=0),
    },
    'send-monthly-reports': {
        'task': 'backend.tasks.send_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=1, minute=0),
    },
    # 'test-every-minute': {
    #      'task': 'backend.tasks.send_monthly_reports',
    #      'schedule': crontab(minute='*'),
    #  },

}
celery.conf.timezone = 'Asia/Kolkata'