__all__ = ['app', 'babel']

from flask import Flask
from flaskext.babel import Babel

import pdfserver.settings
from pdfserver.helpers import LazyView

def url(url_rule, import_name, **options):
    view = LazyView('pdfserver.' + import_name)
    app.add_url_rule(url_rule, view_func=view, **options)

app = Flask(__name__)
app.config.from_object('pdfserver.settings')
app.config.from_envvar('PDFSERVER_SETTINGS', silent=True)
babel = Babel(app)

# Ugly workaround for flask not allowing us to register this later
dbhook = None
@app.teardown_request
def shutdown_session(exception=None):
    if dbhook:
        dbhook()

url('/', 'views.main')
url('/main_table', 'views.main_table', methods=['POST'])
url('/handleform', 'views.handle_form', methods=['POST'])
#url('/confirmdelete', 'views.confirm_delete', methods=['POST'])
url('/delete', 'views.delete', methods=['POST'])
url('/resultpage/<task_id>', 'views.result_page', methods=['GET'])
url('/checkresult/<task_id>', 'views.check_result', methods=['GET'])
url('/download/<task_id>', 'views.download_result', methods=['GET'])
url('/removedownload', 'views.remove_download', methods=['POST'])
