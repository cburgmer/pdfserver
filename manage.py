import sys
import os

from flaskext.script import Server, Manager
#from flaskext.celery import install_commands as install_celery_commands

from pdfserver import app

manager = Manager(app)
#install_celery_commands(manager)

class Runserver(Server):
    def run(self, *args, **kwargs):
        if app.config['DATABASE'].startswith('sqlite:///'):
            file_path = app.config['DATABASE'].replace('sqlite:///', '')
            if not os.path.exists(file_path):
                print >>sys.stderr, ("Database not found, you should probably run "
                                        "'python run.py createdb' first!")
                sys.exit(1)

        if not os.path.exists(app.config['UPLOAD_TO']):
            print >>sys.stderr, ("Upload directory %r not found. "
                                    "You need to create it first!"
                                    % app.config['UPLOAD_TO'])
            sys.exit(1)


        if not app.config['SECRET_KEY']:
            app.config['SECRET_KEY'] = 'development key'

        Server.run(self, *args, **kwargs)

manager.add_command("runserver", Runserver())

@manager.command
def createdb():
    """Creates the database"""
    print >>sys.stderr, "Creating database...",

    from pdfserver import models, database
    database.init_db()

    print >>sys.stderr, "done"


if __name__ == "__main__":
    manager.run()
