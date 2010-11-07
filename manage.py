import sys
import os

from flaskext.script import Server, Manager
#from flaskext.celery import install_commands as install_celery_commands

from pdfserver import app

manager = Manager(app)
#install_celery_commands(manager)

class Runserver(Server):
    def handle(self, app_, *args, **kwargs):
        if app_.config['DATABASE'].startswith('sqlite:///'):
            file_path = app_.config['DATABASE'].replace('sqlite:///', '')
            if not os.path.exists(file_path):
                print >>sys.stderr, ("Database not found, "
                                     "you should probably run "
                                     "'python manage.py createdb' first!")
                sys.exit(1)

        if not os.path.exists(app_.config['UPLOAD_TO']):
            print >>sys.stderr, ("Upload directory %r not found. "
                                    "You need to create it first!"
                                    % app_.config['UPLOAD_TO'])
            sys.exit(1)


        if not app_.config['SECRET_KEY']:
            app_.config['SECRET_KEY'] = 'development key'

        Server.handle(self, app_, *args, **kwargs)

manager.add_command("runserver", Runserver())

@manager.command
def createdb():
    """Creates the database"""
    print >>sys.stderr, "Creating database...",

    from pdfserver import models, faketask, database
    database.init_db()

    print >>sys.stderr, "done"


if __name__ == "__main__":
    manager.run()
