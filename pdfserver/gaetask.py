"""
Task handler for the Google App Engine that emulates celery's task handling.
Results are processed asynchronously and are stored in a database table for
later retrieval.
"""

__all__ = ["NotRegistered", "task"]

import sys
from StringIO import StringIO
from datetime import datetime, timedelta
import pickle
from functools import wraps

from google.appengine.ext import deferred
from google.appengine.ext import db
from google.appengine.runtime import DeadlineExceededError

from pdfserver import app
from pdfserver.gaemodels import USE_1MB_WORKAROUND, MAX_BLOB_SIZE

class TaskResult(db.Model):
    result_blob = db.BlobProperty()
    success = db.BooleanProperty()
    created = db.DateTimeProperty(auto_now=True)
    available = db.BooleanProperty(default=True)
    pending = db.BooleanProperty(default=True)

    def __repr__(self):
        return '<TaskResult %r>' % self.task_id

    def is_available(self):
        return (self.available
                and (datetime.utcnow() - self.created < timedelta(
                                    seconds=app.config['TASK_RESULT_EXPIRES'])))

    @property
    def task_id(self):
        return self.key().id()

    @classmethod
    def get_for_task_id(cls, task_id):
        return cls.get_by_id(task_id)

    @classmethod
    def add(cls, task_result):
        key = task_result.put()
        if USE_1MB_WORKAROUND:
            try:
                cls.store_unsaved_content(task_result)
            except ValueError:
                cls.delete(task_result)
                raise

    @classmethod
    def clean(cls):
        """Clean up old results."""
        oldest_keep_datetime = datetime.utcnow() - timedelta(
                                    seconds=app.config['TASK_RESULT_EXPIRES'])
        for task_result in cls.all().filter('available =', False):
            TaskResult.delete(task_result)
        for task_result in cls.all().filter('created <', oldest_keep_datetime):
            TaskResult.delete(task_result)

    @classmethod
    def delete(cls, task_result):
        db.delete([task_result])
        if USE_1MB_WORKAROUND:
            blobs = []
            for i in range(BLOB_COUNT):
                blob_cls = getattr(sys.modules[__name__],
                                   'TaskResultBlob%d' % i)
                blob = blob_cls.all().filter('task_result =', task_result).get()
                if blob:
                    blobs.append(blob)
            db.delete(blobs)

    @classmethod
    def store_unsaved_content(cls, task_result):
        if not hasattr(task_result, 'unsaved_content'):
            app.logger.debug("Storing slices failed, no content found")
            return

        task_result.unsaved_content.seek(0)
        for i in range(BLOB_COUNT):
            app.logger.debug("Cheating AppEngine, storing blob slices...")
            blob_cls = getattr(sys.modules[__name__], 'TaskResultBlob%d' % i)
            blob = blob_cls(task_result=task_result,
                            blob=db.Blob(task_result.unsaved_content.read(
                                                                MAX_BLOB_SIZE)))
            blob.put()
        if len(task_result.unsaved_content.read(1)) > 0:
            app.logger.debug("Storing slices failed, result too big")
            raise ValueError("Result too big")

    def get_result(self):
        buf = StringIO()
        if USE_1MB_WORKAROUND:
            for i in range(BLOB_COUNT):
                blob_cls = getattr(sys.modules[__name__],
                                   'TaskResultBlob%d' % i)
                slice = blob_cls.all().filter('task_result =', self).get()
                if slice:
                    buf.write(slice.blob)
                else:
                    app.logger.debug("No slice %d" % i)
            return buf.getvalue()
        else:
            return result_blob

    def set_result(self, value):
        app.logger.debug("Setting result with USE_1MB_WORKAROUND=%r" % USE_1MB_WORKAROUND)
        if USE_1MB_WORKAROUND:
            self.unsaved_content = StringIO(value)
        else:
            self.result_blob = db.Blob(value)

    result = property(get_result, set_result)

class TaskResultBlob0(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob1(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob2(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob3(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob4(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob5(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob6(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob7(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob8(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

class TaskResultBlob9(db.Model):
    task_result = db.ReferenceProperty(TaskResult)
    blob = db.BlobProperty()

BLOB_COUNT = 10


tasks = {}
"""Collects all tasks defined by the task decorator."""

def task(func):
    """Decorator for generating a task similar to Celery."""
    @wraps(func, assigned=("__module__", "__name__"))
    def run(self, *args, **kwargs):
        return func(*args, **kwargs)

    # TODO name should be set through class
    #   (see metaclass in celery.task.base.TaskType)
    name = func.__module__ + '.' + func.__name__ 
    cls_dict = dict(run=run,
                    name=name,
                    __module__=func.__module__,
                    __doc__=func.__doc__)
    t = type(func.__name__, (GAETask, ), cls_dict)()
    tasks[name] = t
    return t


class NotRegistered(Exception):
    """Task is not registered."""


class AsyncResult(object):
    def __init__(self, task_id):
        self._task_id = task_id

    def _get_result_from_db(self):
        if not hasattr(self, '_task_result'):
            task_result = TaskResult.get_for_task_id(long(self._task_id))

            if task_result is None:
                raise NotRegistered()

            self._task_result = task_result

        return self._task_result

    def forget(self):
        task_result = self._get_result_from_db()

        task_result.available = False
        TaskResult.add(task_result)

    def ready(self):
        task_result = self._get_result_from_db()
        return not task_result.pending

    def successful(self):
        task_result = self._get_result_from_db()
        return not task_result.pending and task_result.success

    @property
    def result(self):
        task_result = self._get_result_from_db()
        if not task_result.is_available():
            raise NotRegistered("Not available anymore")
        return pickle.loads(task_result.result)

    @property
    def task_id(self):
        return str(self._task_id)

    def available(self):
        """Checks if the result hasn't expired yet."""
        task_result = self._get_result_from_db()
        return task_result.is_available()


def run(name, task_id, *args, **kwargs):
    try:
        output = tasks[name].run(*args, **kwargs)
        success = True
    except (DeadlineExceededError, Exception), e:
        app.logger.debug("Exception during run ... %r" % e)
        output = e
        success = False

    try:
        result = pickle.dumps(output)
        task_result = TaskResult.get_for_task_id(task_id)
        task_result.result = result
        task_result.success = success
        task_result.pending = False
        TaskResult.add(task_result)
    except Exception, e:
        app.logger.debug("Exception storing result ... %r" % e)


class GAETask(object):
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

        # Create an empty result slot and yield id
        task_result = TaskResult(result=None)
        TaskResult.add(task_result)
        task_id = task_result.task_id

        # Run deferred
        deferred.defer(run, cls.name, task_id, *args, **kwargs)

        return cls.AsyncResult(task_id=task_id)

    @classmethod
    def AsyncResult(self, task_id):
        return AsyncResult(task_id)
