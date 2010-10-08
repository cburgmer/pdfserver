#!/usr/bin/python
from wsgiref.handlers import CGIHandler
from pdfserver import app

app.config['SECRET_KEY'] =  # set this to a random string
app.config['DATABASE'] = 'sqlite:///pdfserver.db'
# create a upload folder that is not! readable from the outside
app.config['UPLOAD_TO'] = os.path.join(os.path.dirname(__file__), 'uploads')

CGIHandler().run(app)
