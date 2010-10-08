Pdfserver is a webservice that offers common PDF operations like joining
documents or selecting pages. It is based on the Python based microframework
Flask and depends on pyPdf to manipulate PDFs.

Rationale
=========
Powerful tools to manipulate PDF exist but they are not universally
available on all systems or not simple to use. This server allows anyone to
quickly solve most common PDF operations over the web.

If you don't trust other servers with your data, deploy a copy yourself!

Example
=======
See http://cburgmer.nfshost.com/pdfserver/ for an example installation.

Dependencies
============
* Python 2.5, http://www.python.org
* Flask (tested on 0.6), http://flask.pocoo.org/
* Flask-Babel, http://packages.python.org/Flask-Babel/
* SQLAlchemy (probably >= 0.6.0), http://www.sqlalchemy.org/
* pyPdf (tested with 1.12, but needs git~20091021 for "N pages on one"), 
  http://pybrary.net/pyPdf/

Optionally
----------
* python-reportlab (tested with 2.4) for adding watermarks,
  http://www.reportlab.com/software/opensource/rl-toolkit/

Already included
----------------
* jQuery & jQuery UI (tested with 1.8.4) (both already shipped with pdfserver),
  needs at least UI core, "Sortable" and "Dialog" from jQuery UI,
  http://jquery.com/
* jQuery plugin: Validation,
  http://bassistance.de/jquery-plugins/jquery-plugin-validation/

Features
========
* Simple, yet powerful
* Designed to work with&without Javascript
* N pages on one
* Joining of files
* Selecting pages & page ranges
* Rotate pages
* Add watermark to pages

Changes
=======
0.3

* "N pages on one" feature
* Move to Flask from Django

0.2.1

* Page rotation
* Watermark feature
* Page range validation

Deploy
======
Install this application with::

    $ python setup.py install pdfserver

You can simply run the development server with::

    $ python run.py createdb
    $ mkdir uploads
    $ python run.py

General
-------

1. Make sure the given upload directory and database can be written to and are
   not accessible from the outside (if on a public server).

2. When not in debug mode make sure to serve static files under ``static``.

3. Give a ``SECRET_KEY`` and keep it secret so that sessions can be signed and
   users cannot see files uploaded by others.

Serve as CGI
------------

See pdfserver.cgi for an example on how to run pdfserver through the
traditional CGI interface.

Contact
=======
Please report bugs to http://github.com/cburgmer/pdfserver/issues.

Christoph Burgmer <cburgmer (at) ira uka de>
