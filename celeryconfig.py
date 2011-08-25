# See http://docs.celeryproject.org/en/latest/tutorials/otherqueues.html#sqlalchemy and http://celeryq.org/docs/configuration.html
BROKER_TRANSPORT = "sqlakombu.transport.Transport"
BROKER_HOST = "sqlite:///celery.db"
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celery.db"
CELERY_IMPORTS = ("pdfserver.tasks", )
# Expire results after 10 minutes (privacy issue with exposed downloads)
#  See documentation under 
#  http://docs.celeryproject.org/en/latest/configuration.html#celery-task-result-expires
CELERY_TASK_RESULT_EXPIRES = 10 * 60
