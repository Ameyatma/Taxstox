import os
from celery import Celery
from celery.schedules import crontab

# Broker and result backend both come from environment variables.
# Taxstox sets REDIS_URL via .env or Docker env; fall back to local redis.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "stock_intelligence",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.overnight_pipeline",
        "tasks.rd_agent_tasks",
    ],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # A long-running mining cycle should not be re-delivered mid-flight; combined with
    # the generous time limit this keeps a worker restart from double-running research.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=60 * 60,
    task_soft_time_limit=55 * 60,
    # Do not let the beat schedule lose its place across restarts.
    beat_schedule_filename='celerybeat-schedule',
)

# All times are UTC. Celery Beat owns scheduling, so these run in the dedicated
# `beat` container and survive worker restarts.
celery_app.conf.beat_schedule = {
    # 11:30 UTC is 17:00 IST, an hour and a half after the NSE closes at 15:30 IST.
    # The gap lets the exchange publish final settlement prices and Yahoo ingest them,
    # and 17:00 IST is the standard NSE end-of-day reporting time.
    'nightly-overnight-pipeline': {
        'task': 'tasks.overnight_pipeline.run_overnight_pipeline',
        'schedule': crontab(minute=30, hour=11, day_of_week='mon-fri'),
        'options': {'expires': 3600},
    },
    # Weekend research: propose 3 factors, backtest them, deploy any that pass the gate.
    'weekly-rd-agent-mining': {
        'task': 'tasks.rd_agent_tasks.run_autonomous_mining_cycle',
        'schedule': crontab(minute=0, hour=0, day_of_week='sunday'),
        'kwargs': {'cycles': 3},
        'options': {'expires': 3600},
    },
}
