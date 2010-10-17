__all__ = ['handle_pdfs_task', 'TaskRevokedError', 'NotRegistered']

from pdfserver.util import handle_pdfs
from pdfserver import app
task = __import__(app.config['TASK_HANDLER'], fromlist='task').task

if app.config['TASK_HANDLER'] == 'celery.decorators':
    from celery.exceptions import TaskRevokedError, NotRegistered

elif app.config['TASK_HANDLER'] == 'pdfserver.faketask':
    from pdfserver.faketask import NotRegistered
    class TaskRevokedError(Exception):
        pass


@task
def handle_pdfs_task(files_handles, page_range_text=None, pages_sheet=1,
                     rotate=0, overlay=None):
    output = handle_pdfs(files_handles, page_range_text=page_range_text,
                         pages_sheet=pages_sheet, rotate=rotate,
                         overlay=overlay)
    return output.encode('zlib')
