import os
import glob
package_path = os.path.join(os.path.dirname(__file__), 'pdfserver')

DATABASE = 'sqlite:////tmp/pdfserver_test.db'
SECRET_KEY = "test key"
UPLOAD_TO = '/tmp'
MODELS = 'pdfserver.models'

from celery.decorators import task
TASK_HANDLER = 'celery.decorators'

translation_paths = os.path.join(package_path, 'translations')
SUPPORTED_TRANSLATIONS = ['en'] + [s.replace(translation_paths + '/', '')
                                   for s in glob.glob(translation_paths + '/*')]
