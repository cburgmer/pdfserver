# -*- coding: utf-8 -*-
import re

from flask import g, request, Response, session, render_template
from flask import abort, redirect, url_for, jsonify
from werkzeug import wrap_file
from werkzeug.exceptions import InternalServerError, Gone, NotFound

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
    file_ids = session.get('file_ids', [])
    return Upload.get_for_ids(file_ids)

@templated('main.html')
def main():
    files = _get_uploads()
    return {'uploads': files}

def upload_file():
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
    if request.form.get('delete', False):
        upload = _get_upload()

        session['file_ids'].remove(upload.id)
        session.modified = True
        Upload.delete(upload)
        Upload.commit()

    return redirect(url_for('main'))

@templated('confirm_delete_all.html')
def confirm_delete_all():
    files = _get_uploads()
    return {'uploads': files}

def delete_all():
    if request.form.get('delete', False):
        files = _get_uploads()

        session['file_ids'] = []
        for upload in files:
            Upload.delete(upload)
        Upload.commit()

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

    def order_files(files, order):
        try:
            order = map(int, order)
        except ValueError:
            app.logger.debug("Error converting to ints: %r" % order)
        if (not order or len(files) != len(order) or min(order) != 1 or
            max(order) != len(files)):
            order = range(1, len(files)+1)

        return ((idx, files[idx-1]) for idx in order)

    file_ids = session.get('file_ids', [])

    # If user clicked on button but no files were uploaded
    if not file_ids:
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
    order = request.form.getlist('file[]')
    indices, file_ids = zip(*order_files(file_ids, order))
    pages = [request.form.get('pages_%d' % item_idx, "")
                    for item_idx in indices]

    # Do the actual work
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
                app.logger.debug("Result not successful: %r" % result)
                raise InternalServerError(unicode(result.result))
    except NotRegistered:
        app.logger.debug("Result not registered %r" % task_id)
        raise NotFound()

    return redirect(url_for('result_page', task_id=task_id))

def remove_download():
    task_id = request.form.get('task_id', None)
    app.logger.debug("task_id %r" % task_id)
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
