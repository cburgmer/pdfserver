from google.appengine.ext.webapp.util import run_wsgi_app
from pdfserver import app

app.config['MODELS'] = 'pdfserver.gaemodels'
app.config['TASK_HANDLER'] = 'pdfserver.gaetask'
app.config['SECRET_KEY'] =  # set this to a random string
run_wsgi_app(app)
