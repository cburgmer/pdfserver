#!/usr/bin/python
import os

## Include modules from the virtualenv (in same directory) with this runner
#activate_this = os.path.join(os.path.dirname(__file__), 
#                             'virtualenv/bin/activate_this.py')
#execfile(activate_this, dict(__file__=activate_this))

from wsgiref.handlers import CGIHandler
from pdfserver import app

app.config['SECRET_KEY'] =  # set this to a random string
app.config['DATABASE'] = 'sqlite:///pdfserver.db'
# create a upload folder that is not! readable from the outside
app.config['UPLOAD_TO'] = os.path.join(os.path.dirname(__file__), 'uploads')

CGIHandler().run(app)
