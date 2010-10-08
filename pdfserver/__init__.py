from flask import Flask
from flaskext.babel import Babel

import pdfserver.settings

__all__ = ['app', 'babel']

app = Flask(__name__)
app.config.from_object('pdfserver.settings')
app.config.from_envvar('PDFSERVER_SETTINGS', silent=True)
babel = Babel(app)

import pdfserver.views
