import os
import glob
package_path = os.path.dirname(__file__)

DATABASE = 'sqlite:///%s' % os.path.join(package_path, '..', 'pdfserver.db')
DEBUG = False
SECRET_KEY = None
UPLOAD_TO = os.path.join(package_path, '..', 'uploads')
MODELS = 'pdfserver.models'

translation_paths = os.path.join(os.path.dirname(__file__), 'translations')
SUPPORTED_TRANSLATIONS = ['en'] + [s.replace(translation_paths + '/', '')
                                   for s in glob.glob(translation_paths + '/*')]
