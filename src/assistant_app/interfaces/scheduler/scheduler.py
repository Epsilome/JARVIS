from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from assistant_app.config.settings import settings

jobstores = {"default": SQLAlchemyJobStore(url=settings.DATABASE_URL)}
scheduler = BackgroundScheduler(jobstores=jobstores)
