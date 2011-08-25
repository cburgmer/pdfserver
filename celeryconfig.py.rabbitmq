# See http://celeryq.org/docs/configuration.html
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "myuser"
BROKER_PASSWORD = "mypassword"
BROKER_VHOST = "myvhost"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("pdfserver.tasks", )
# Expire results after 10 minutes (privacy issue with exposed downloads)
#  See documentation under 
#  http://celeryq.org/docs/configuration.html#std:setting-CELERY_TASK_RESULT_EXPIRES
CELERY_TASK_RESULT_EXPIRES = 10 * 60
# (RabbitMQ >= 2.1.0) expire results after 10 minutes
CELERY_AMQP_TASK_RESULT_EXPIRES = 10 * 60
