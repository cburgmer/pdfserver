import os
import glob
package_path = os.path.dirname(__file__)

DATABASE = 'sqlite:///%s' % os.path.join(package_path, '..', 'pdfserver.db')
DEBUG = False
SECRET_KEY = None
UPLOAD_TO = os.path.join(package_path, '..', 'uploads')
# MAX_CONTENT_LENGTH = 10485760 # sets maximum upload size to 10 MB
MODELS = 'pdfserver.models'

# Asynchronous task settings
try:
    from celery.decorators import task
    TASK_HANDLER = 'celery.decorators'
except ImportError:
    TASK_HANDLER = 'pdfserver.faketask'
# Expire results after 10 minutes (currently only respected by faketask)
TASK_RESULT_EXPIRES = 10 * 60

translation_paths = os.path.join(os.path.dirname(__file__), 'translations')
SUPPORTED_TRANSLATIONS = ['en'] + [s.replace(translation_paths + '/', '')
                                   for s in glob.glob(translation_paths + '/*')]
