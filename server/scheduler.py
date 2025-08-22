# server/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from server.tasks.finance_reminders import process_payment_reminders

def init_scheduler(app):
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(process_payment_reminders, "cron", hour=6, minute=0)
    sched.start()
    return sched
