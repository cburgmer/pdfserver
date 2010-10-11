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

url('/', 'views.main')
url('/upload', 'views.upload_file', methods=['POST'])
#url('/confirmdelete', 'views.confirm_delete', methods=['POST'])
url('/delete', 'views.delete', methods=['POST'])
url('/confirmdelete/all', 'views.confirm_delete_all', methods=['POST'])
url('/deleteall', 'views.delete_all', methods=['POST'])
url('/combine', 'views.combine_pdfs', methods=['POST'])
