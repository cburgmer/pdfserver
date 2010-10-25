"""
Fake task handler that emulates celery's task handling.
Results are processed synchronously and are stored in a database table for later
retrieval.
"""

__all__ = ["NotRegistered", "task"]

from datetime import datetime, timedelta
import pickle

from sqlalchemy import Table, Column, Integer, LargeBinary, Boolean, DateTime
from sqlalchemy.orm import mapper
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_, or_

from pdfserver.database import metadata, db_session
from pdfserver import app

class TaskResult(object):
    query = db_session.query_property()

    def __init__(self, result=None, success=None, created=None, available=True):
        self.result = result
        self.success = success
        self.created = created or datetime.utcnow()
        self.available = available

    def __repr__(self):
        return '<TaskResult %r>' % self.task_id

    def is_available(self):
        return (self.available
                and (datetime.utcnow() - self.created < timedelta(
                                    seconds=app.config['TASK_RESULT_EXPIRES'])))

    @classmethod
    def get_for_task_id(cls, task_id):
        try:
            return cls.query.filter(cls.task_id == task_id).one()
        except NoResultFound:
            return None

    @classmethod
    def clean(cls):
        """Clean up old results."""
        oldest_keep_datetime = datetime.utcnow() - timedelta(
                                    seconds=app.config['TASK_RESULT_EXPIRES'])
        cls.query.filter(or_(cls.created < oldest_keep_datetime,
                             cls.available == False)).delete()
        db_session.commit()

    @classmethod
    def add(cls, task_result):
        db_session.add(task_result)

    @classmethod
    def delete(cls, task_result):
        db_session.delete(task_result)

    @classmethod
    def commit(cls):
        db_session.commit()


task_results = Table('task_results', metadata,
    Column('task_id', Integer, primary_key=True),
    Column('result', LargeBinary),
    Column('success', Boolean),
    Column('created', DateTime),
    Column('available', Boolean),
    # Use AUTOINCREMENT for sqlite3 to yield globally unique ids
    #   -> new ids cannot take on ids of deleted items, security issue!
    sqlite_autoincrement=True,
)

mapper(TaskResult, task_results)


def task(func):
    """Decorator for generating a pseudo task, similar to Celery."""
    #@wraps(func, assigned=("__module__", "__name__")) # TODO Python2.5 compatibility
    def run(self, *args, **kwargs):
        return func(*args, **kwargs)

    cls_dict = dict(run=run,
                    __module__=func.__module__,
                    __doc__=func.__doc__)
    return type(func.__name__, (FakeTask, ), cls_dict)()


class NotRegistered(Exception):
    """Task is not registered."""


class FakeAsyncResult(object):
    def __init__(self, task_id):
        self._task_id = task_id

    def _get_result_from_db(self):
        if not hasattr(self, '_task_result'):
            task_result = TaskResult.get_for_task_id(self.task_id)

            if task_result is None:
                raise NotRegistered()

            self._task_result = task_result

        return self._task_result

    def forget(self):
        task_result = self._get_result_from_db()

        task_result.available = False
        TaskResult.add(task_result)

    def ready(self):
        # Synchronous call -> always ready
        return True

    def successful(self):
        task_result = self._get_result_from_db()
        return task_result.success

    @property
    def result(self):
        task_result = self._get_result_from_db()
        if not task_result.is_available():
            raise NotRegistered("Not available any more")
        return pickle.loads(task_result.result)

    @property
    def task_id(self):
        return str(self._task_id)

    def available(self):
        """Checks if the result hasn't expired yet."""
        task_result = self._get_result_from_db()
        return task_result.is_available()


class FakeTask(object):
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def delay(cls, *args, **kwargs):
        return cls.apply_async(args, kwargs)

    @classmethod
    def apply_async(cls, args=None, kwargs=None, **options):
        args = args or []
        kwargs = kwargs or {}
        try:
            output = cls()(*args, **kwargs)
            success = True
        except Exception, e:
            output = e
            success = False

        result = pickle.dumps(output)
        task_result = TaskResult(result=result, success=success)
        TaskResult.add(task_result)
        TaskResult.commit()

        return cls.AsyncResult(task_id=task_result.task_id)

    @classmethod
    def AsyncResult(self, task_id):
        return FakeAsyncResult(task_id)
