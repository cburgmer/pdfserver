import sys
import os

from pdfserver import app

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and sys.argv[1] == 'createdb':
            print "Creating database...",

            from pdfserver import database
            database.init_db()

            print "done"
            sys.exit(0)
        else:
            print >> sys.stderr, "Illegal command"
            sys.exit(1)

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

    app.run(debug=True)
