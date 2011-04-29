Pdfserver is a webservice that offers common PDF operations like joining
documents, selecting pages or "n pages on one". It is built on top of the
Python based microframework Flask and depends on pyPdf to manipulate PDFs.

Rationale
=========
Powerful tools to manipulate PDF exist but they are not universally
available on all systems or not simple to use. This server allows anyone to
quickly solve most common PDF operations over the web.

If you don't trust other servers with your data, deploy a copy yourself!

Example
=======
See http://pdfserverapp.appspot.com/ for an example installation.

Dependencies
============
(see ``requirements.txt``)

* Python (>= 2.5, < 3.0), http://www.python.org
* Flask (tested on 0.6), http://flask.pocoo.org/
* Flask-Babel, http://packages.python.org/Flask-Babel/
* Flask-Script (>= 0.3.1), http://bitbucket.org/danjac/flask-script
* SQLAlchemy (probably >= 0.6.0), http://www.sqlalchemy.org/
* pyPdf (>= 1.13),
  http://pybrary.net/pyPdf/

Optionally
----------
* python-reportlab (tested with 2.4) for adding watermarks,
  http://www.reportlab.com/software/opensource/rl-toolkit/
* celery (tested with 2.0.0) for asynchronous request handling (not needed on
  Google App Engine), http://celeryq.org/

Already included
----------------
* jQuery & jQuery UI (tested with 1.8.4) (both already shipped with pdfserver),
  needs at least UI core, "Sortable" and "Dialog" from jQuery UI,
  http://jquery.com/
* jQuery plugin: Validation,
  http://bassistance.de/jquery-plugins/jquery-plugin-validation/
* jNotify jQuery Plug-in, unobtrusive notification system
  http://www.givainc.com/labs/jnotify_jquery_plugin.htm

Features
========
* Simple, yet powerful
* Designed to work with&without Javascript
* N pages on one
* Joining of files
* Selecting pages & page ranges
* Rotate pages
* Add watermark to pages
* Runs on the Google App Engine
* Handle builds asynchronously

Changes
=======
0.5

* Fix setup.py statics
* Show warning if cookies not enabled
* Update pyPdf dependency
* Enable testing for celery task backend

0.4

* Handle upload and remove actions through Ajax
* Support for asynchronous PDF generation
* Fix max upload size handling for App Engine
* Unittests
* Action messages

0.3

* Renamed to "pdfserver" from "django-pdfserver"
* "N pages on one" feature
* Move to Flask from Django
* Google App Engine support

0.2.1

* Page rotation
* Watermark feature
* Page range validation

Deploy
======

Download and extract the soure code.

Create a virtualenv in the extracted folder and install requirements::

    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt

You can simply run the development server with::

    $ python manage.py createdb
    $ mkdir uploads
    $ python manage.py runserver

General
-------

1. Make sure the given upload directory and database can be written to and are
   not accessible from the outside (if on a public server).

2. When not in debug mode make sure to serve static files under ``static``.

3. Give a ``SECRET_KEY`` and keep it secret so that sessions can be signed and
   users cannot see files uploaded by others.

4. Create the database by running::

    $ python manage.py createdb

Celery
------
For optional, asynchronous generation of the resulting PDF install celery and
(as default broker) RabbitMQ (see 
http://celeryq.org/docs/getting-started/broker-installation.html).

Run celeryd from the project's directory to handle tasks asynchronously::

    $ celeryd

The Google App Engine has its own dereferred library which is automatically
used.

Serve as CGI
------------

See pdfserver.cgi for an example on how to run pdfserver through the
traditional CGI interface.

Google App Engine
-----------------

For pdfserver to run on the App Engine you need to download and copy
dependencies locally. Run the following in the extracted folder::

    # Get dependencies
    $ mkdir tmp
    $ pip install -r requirements.txt distribute --build=tmp --src=tmp \
      --no-install --ignore-installed
    $ mv tmp/Babel/babel/ tmp/Flask/flask/ tmp/Flask-Babel/flaskext/ \
      tmp/Jinja2/jinja2/ tmp/pypdf/pyPdf/ tmp/pytz/pytz \
      tmp/speaklater/speaklater.py tmp/Werkzeug/werkzeug/ \
      tmp/reportlab/src/reportlab/ tmp/distribute/pkg_resources.py .
    $ rm -rf tmp
    # Add a secret key
    $ $EDITOR appengine.py
    # Choose your application name
    $ $EDITOR app.yaml
    # Run the development server
    $ /usr/local/google_appengine/dev_appserver.py .
    # Finally upload
    $ /usr/local/google_appengine/appcfg.py update .

If tasks won't get executed (you can check under
http://localhost:8080/_ah/admin/tasks?queue=default), you might got hitten
by bug http://code.google.com/p/appengine-mapreduce/issues/detail?id=9,
see workaround there.

Contact
=======
Please report bugs to http://github.com/cburgmer/pdfserver/issues.

Christoph Burgmer <cburgmer (at) ira uka de>
