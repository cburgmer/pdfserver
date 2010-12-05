# -*- coding: utf-8 -*-
import re
from operator import attrgetter

from flask import g, request, Response, session, render_template
from flask import abort, redirect, url_for, jsonify
from flaskext.babel import gettext
from werkzeug import wrap_file
from werkzeug.exceptions import InternalServerError, MethodNotAllowed, Gone, \
                                NotFound

from pyPdf import PdfFileWriter, PdfFileReader

from pdfserver import app, babel
Upload = __import__(app.config['MODELS'], fromlist='Upload').Upload
from pdfserver.util import templated
from pdfserver.tasks import handle_pdfs_task, NotRegistered

@babel.localeselector
def get_locale():
    # Get language from the user accept header the browser transmits.
    return request.accept_languages.best_match(
                                        app.config['SUPPORTED_TRANSLATIONS'])

def _get_upload():
    app.logger.debug("IDS %r" % request.form.get('id', None))

    try:
        id = long(request.form.get('id', None))
    except ValueError:
        app.logger.debug("Invalid id specified: %r"
                         % request.form.get('id', None))
        raise abort(404)

    file_ids = session.get('file_ids', [])
    app.logger.debug(file_ids)
    if id not in file_ids:
        app.logger.debug("No upload with id %r for user" % id)
        raise abort(404)

    upload = Upload.get_for_id(id)
    if upload:
        return upload
    else:
        app.logger.debug("Upload with id %r doesn't exist" % id)
        raise abort(404)

def _get_uploads():
    file_ids = map(int, session.get('file_ids', []))
    if not file_ids:
        return []
    return Upload.get_for_ids(file_ids)

def _order_files(files):
    """Return a mapping for each id given by POST data.

    Appends missing ids to the end of the given order.
    """
    files_order = []

    file_id_map = dict((upload.id, upload) for upload in files)

    # Get user selected order from form
    order = request.form.getlist('file[]')
    for id in order:
        try:
            id = int(id)
        except ValueError:
            continue
        if id and id in file_id_map:
            files_order.append(file_id_map[id])
            del file_id_map[id]

    # Append missing ids
    files_order.extend(file_id_map.values())

    return files_order

@templated('main.html')
def main():
    files = _get_uploads()
    session['has_cookies'] = 1
    return {'uploads': files}

def main_table():
    # Get user defined order
    files = _order_files(_get_uploads())

    return jsonify(content=render_template('uploads.html',
                                           uploads=files))

def handle_form():
    action = request.form.get('form_action', 'upload')
    app.logger.debug(action)
    if action == 'upload':
        return upload_file()
    elif action == 'confirm_deleteall':
        return confirm_delete_all()
    elif action == 'deleteall':
        return delete_all()
    elif action == 'combine':
        return combine_pdfs()
    elif action == 'cancel':
        return main()
    else:
        raise MethodNotAllowed()

def upload_file():
    if not session.get('has_cookies', 0) == 1:
        app.logger.debug("No cookie found")
        return Response('<html><body><span id="cookies">'
                        + gettext('Please activate cookies '
                                  'so your uploads can be linked to you.')
                        + '</span></body></html>')

    if 'file' in request.files and request.files['file']:
        app.logger.info("Upload form is valid")
        upload = Upload()

        # save original name
        upload.store_file(request.files['file'])

        Upload.add(upload)
        Upload.commit()

        # link to session
        file_ids = session.get('file_ids', [])
        file_ids.append(upload.id)
        session['file_ids'] = file_ids

        app.logger.info("Saved upload: %s" % upload)
    else:
        app.logger.error("No file specified")

    return redirect(url_for('main'))

#@templated('confirm_delete.html')
#def confirm_delete():
    #files = _get_uploads()
    #return {'uploads': files}

def delete():
    upload = _get_upload()

    session['file_ids'].remove(upload.id)
    session.modified = True
    Upload.delete(upload)
    Upload.commit()

    return main_table()

@templated('confirm_delete_all.html')
def confirm_delete_all():
    files = _get_uploads()
    return {'uploads': files}

def delete_all():
    app.logger.debug("Deleting all files")
    files = _get_uploads()

    session['file_ids'] = []
    for upload in files:
        Upload.delete(upload)
    Upload.commit()

    if request.is_xhr:
        return main_table()
    else:
        return redirect(url_for('main'))

def _respond_with_pdf(output):
    # TODO get proper file name
    response = Response(content_type='application/pdf')
    response.headers.add('Content-Disposition',
                         'attachment; filename=combined.pdf')

    response.data = output

    app.logger.debug("Wrote %d bytes" % len(response.data))

    return response

def combine_pdfs():
    files = _get_uploads()

    # If user clicked on button but no files were uploaded
    if not files:
        return redirect(url_for('main'))

    # Get options
    try:
        # make sure value is multiple of 90
        rotate = int(request.form.get('rotate', '0')) / 90 * 90
    except ValueError:
        rotate = 0
    try:
        # make sure value is multiple of 90
        pages_sheet = int(request.form.get('pages_sheet', '1'))
        if not pages_sheet in (1, 2, 4, 6, 9, 16):
            raise ValueError
    except ValueError:
        pages_sheet = 1

    text_overlay = request.form.get('text_overlay', None)

    app.logger.debug(u"Parameters: %d pages on one, rotate %d°, text overlay %r"
                     % (pages_sheet, rotate, text_overlay))


    # Get pdf objects and arrange in the user selected order, then get ranges
    files = _order_files(files)

    pages = [request.form.get('pages_%d' % upload.id, "")
                    for upload in files]

    # Do the actual work
    file_ids = map(attrgetter('id'), files)
    resp = handle_pdfs_task.apply_async((file_ids,
                                         pages,
                                         pages_sheet,
                                         rotate,
                                         text_overlay))
    # Save task in session and keep the open task list small
    session['tasks'] = session.get('tasks', [])[-9:] + [resp.task_id]

    if request.is_xhr:
        return jsonify(ready=False, task_id=resp.task_id,
                       url=url_for('check_result', task_id=resp.task_id))
    else:
        return redirect(url_for('result_page', task_id=resp.task_id))

def result_page(task_id):
    """
    Non-Javascript result page
    """
    if task_id not in session.get('tasks', []):
        app.logger.debug("Valid tasks %r" % session.get('tasks', []))
        raise NotFound()

    param = {'task_id': task_id,
             'ready': handle_pdfs_task.AsyncResult(task_id).ready()}
    return render_template('download.html', **param)

def check_result(task_id):
    if task_id not in session.get('tasks', []):
        app.logger.debug("Valid tasks %r" % session.get('tasks', []))
        raise NotFound()

    result = handle_pdfs_task.AsyncResult(task_id)
    if result.ready():
        url = url_for('download_result', task_id=task_id)
    else:
        url = ''
    return jsonify(ready=result.ready(), url=url, task_id=task_id,
                   success=result.successful())

def download_result(task_id):
    if task_id not in session.get('tasks', []):
        app.logger.debug("Valid tasks %r" % session.get('tasks', []))
        raise NotFound()

    try:
        result = handle_pdfs_task.AsyncResult(task_id)
        if result.ready():
            if hasattr(result, 'available') and not result.available():
                raise Gone("Result expired. "
                        "You probably waited too long to download the file.")

            if result.successful():
                output = result.result
                return _respond_with_pdf(output.decode('zlib'))
            else:
                app.logger.debug("Result not successful: %r" % result.result)
                raise InternalServerError(unicode(result.result))
    except NotRegistered:
        app.logger.debug("Result not registered %r" % task_id)
        raise NotFound()

    return redirect(url_for('result_page', task_id=task_id))

def remove_download():
    task_id = request.form.get('task_id', None)
    if task_id not in session.get('tasks', []):
        app.logger.debug("Valid tasks %r" % session.get('tasks', []))
        raise NotFound()

    result = handle_pdfs_task.AsyncResult(task_id)
    session['tasks'].remove(task_id)
    session.modified = True
    try:
        if hasattr(result, 'forget'):
            result.forget()
    except NotRegistered:
        app.logger.debug("Result not registered %r" % task_id)
        raise NotFound()
    return jsonify(status="OK")
