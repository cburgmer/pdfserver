Pdfserver is a webservice that offers common PDF operations like joining
documents or selecting pages. It is based on Django and depends on pyPdf to
manipulate PDFs.

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
* Django (tested with 1.2), http://www.djangoproject.com/
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
- Simple, yet powerful
- Designed to work with&without Javascript
- N pages on one
- Joining of files
- Selecting pages & page ranges
- Rotate pages
- Add watermark to pages

Deploy
======
You can install this application with::

    $ python setup.py install pdfserver

To start a project around pdfserver run the following steps:

1. Create a new project::

    $ django-admin startproject myserver
  
2. Edit settings to fit pdfserver's needs (``myserver/settings.py``) following
   the example in ``example_settings.py``. Choose ``sqlite3`` for the database 
   if in doubt.

3. Create the database::

    $ cd myserver
    $ python manage.py syncdb

4. Make sure the given upload directory can be written to and not accessible 
   from the outside (if on a public server).

5. For a test installation you can run::

    $ python manage.py runserver

When not in debug mode make sure to serve static files under ``media/js/*``
and ``media/css/*``.

Contact
=======
Please report bugs to http://github.com/cburgmer/pdfserver/issues.

Christoph Burgmer <cburgmer (at) ira uka de>