# server/tasks/__init__.py
from celery import Celery
from celery.schedules import crontab
from server import create_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery

app = create_app()
celery = make_celery(app)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every day at 9 AM
    sender.add_periodic_task(
        crontab(hour=9, minute=0),
        process_payment_reminders.s()
    )

@celery.task
def process_payment_reminders():
    from server.tasks.finance_reminders import process_payment_reminders
    process_payment_reminders()