from backend.app import create_app
from celery.schedules import crontab

flask_app = create_app()

from backend.extensions import celery

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