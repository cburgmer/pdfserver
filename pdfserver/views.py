# -*- coding: utf-8 -*-
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from flask import g, request, Response, session, flash, abort, redirect, url_for
from flaskext.babel import gettext as tr
from werkzeug import wrap_file

from pyPdf import PdfFileWriter, PdfFileReader

from pdfserver import app, babel
Upload = __import__(app.config['MODELS'], fromlist='Upload').Upload
from pdfserver.util import get_overlay_page, n_pages_on_one, templated

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
        flash(tr('Uploaded your file "%(filename)s" successfully.',
                 filename=upload.filename))
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

        flash(tr('Deleted file "%(filename)s".', filename=upload.filename))

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

        flash(tr('Deleted all files.'))

    return redirect(url_for('main'))

def combine_pdfs():

    def order_files(files, order):
        order = map(int, re.findall(r'\d+', order))

        if (not order or len(files) != len(order) or min(order) != 1 or
            max(order) != len(files)):
            order = range(1, len(files)+1)

        return ((idx, files[idx-1]) for idx in order)

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
    if text_overlay:
        overlay = get_overlay_page(text_overlay)
    else:
        overlay = None

    app.logger.debug(u"Parameters: %d pages on one, rotate %d°, text overlay %r"
                     % (pages_sheet, rotate, text_overlay))

    output = PdfFileWriter()

    # Get pdf objects and arrange in the user selected order, then parse ranges
    order = request.form.get('order', "")
    for item_idx, upload in order_files(files, order):
        f = upload.get_file()
        pdf_obj = PdfFileReader(f)
        page_count = pdf_obj.getNumPages()

        # Get page ranges
        pages = request.form.get('pages_%d' % item_idx, "")
        page_ranges = []
        if pages:
            ranges = re.findall(r'\d+\s*-\s*\d*|\d*\s*-\s*\d+|\d+', pages)
            for pages in ranges:
                match_obj = re.match(r'^(\d*)\s*-\s*(\d*)$', pages)
                if match_obj:
                    from_page, to_page = match_obj.groups()
                    if from_page:
                        from_page_idx = max(int(from_page)-1, 0)
                    else:
                        from_page_idx = 0
                    if to_page:
                        to_page_idx = min(int(to_page), page_count)
                    else:
                        to_page_idx = page_count

                    page_ranges.append(range(from_page_idx, to_page_idx))
                else:
                    page_idx = int(pages)-1
                    if page_idx >= 0 and page_idx < page_count:
                        page_ranges.append([page_idx])
        else:
            page_ranges = [range(pdf_obj.getNumPages())]

        # Extract pages from PDF
        pages = []
        for page_range in page_ranges:
            for page_idx in page_range:
                pages.append(pdf_obj.getPage(page_idx))

        # Apply operations
        if pages_sheet > 1 and pages and hasattr(pages[0].mediaBox, 'getWidth'):
            pages = n_pages_on_one(pages, pages_sheet)
        elif pages_sheet > 1 and not hasattr(pages[0].mediaBox, 'getWidth'):
            app.logger.debug("pyPdf too old, not merging pages onto one")
        if rotate:
            app.logger.debug("rotate, clockwise, %r " % rotate)
            map(lambda page: page.rotateClockwise(rotate), pages)
        if overlay:
            map(lambda page: page.mergePage(overlay), pages)

        map(output.addPage, pages)

    # TODO get proper file name
    response = Response(content_type='application/pdf')
    response.headers.add('Content-Disposition',
                         'attachment; filename=combined.pdf')

    buffer = StringIO()
    output.write(buffer)
    response.data = buffer.getvalue()

    app.logger.debug("Wrote %d bytes" % len(response.data))

    return response
