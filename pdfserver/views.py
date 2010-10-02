# -*- coding: utf-8 -*-
import logging
import re

from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms.models import save_instance
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseNotAllowed, Http404)
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from pyPdf import PdfFileWriter, PdfFileReader

from pdfserver.models import Upload
from pdfserver.forms import UploadForm
from pdfserver.util import get_overlay_page, n_pages_on_one

def _get_upload(request):
    try:
        id = int(request.POST.get('id', None))
    except ValueError:
        raise Http404()

    file_ids = request.session.get('file_ids', [])
    if id not in file_ids:
        raise Http404()

    return get_object_or_404(Upload, id=id)

def _get_uploads(request):
    file_ids = request.session.get('file_ids', [])
    return Upload.objects.filter(id__in=file_ids)

@csrf_protect
def main(request):
    files = _get_uploads(request)

    response = render_to_response('main.html',
                                {
                                 'uploads': files,
                                 'form': UploadForm(),
                                },
                                context_instance=RequestContext(request))
    if files:
        response['Cache-Control'] = 'no-cache'
        # TODO response['Expires'] = 
    return response

def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            logging.info("Upload form is valid: %s" % form)
            upload = Upload()

            file_obj = form.files['file']
            # save original name
            upload.filename = file_obj.name

            # save pdf page count
            try:
                file_obj.open('r')
                pdf_obj = PdfFileReader(file_obj)
                upload.page_count = pdf_obj.getNumPages()
                file_obj.close()
            except Exception, e:
                pass

            save_instance(form, upload)

            # link to session
            file_ids = request.session.get('file_ids', [])
            file_ids.append(upload.id)
            request.session['file_ids'] = file_ids

            logging.info("Saved upload: %s" % upload)
        else:
            logging.error("invalid form: %s" % form)
            logging.error("form errors: %s" % form.errors)

    return HttpResponseRedirect(reverse('uploads'))

#@csrf_protect
#def confirm_delete(request):
    #if request.method != 'POST':
        #return HttpResponseNotAllowed(['POST'])

    #upload = _get_upload(request)
    #return render_to_response('confirm_delete.html', {'upload': upload},
                              #RequestContext(request))

@csrf_protect
def delete(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.POST.get('delete', False):
        upload = _get_upload(request)

        upload.file.delete()
        upload.delete()

    return HttpResponseRedirect(reverse('uploads'))

@csrf_protect
def confirm_delete_all(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    files = _get_uploads(request)
    return render_to_response('confirm_delete_all.html', {'uploads': files},
                              RequestContext(request))

@csrf_protect
def delete_all(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.POST.get('delete', False):
        files = _get_uploads(request)

        for upload in files:
            upload.file.delete()
            upload.delete()

    return HttpResponseRedirect(reverse('uploads'))

@csrf_protect
def combine_pdfs(request):

    def order_files(files, order):
        order = map(int, re.findall(r'\d+', order))

        if (not order or len(files) != len(order) or min(order) != 1 or
            max(order) != len(files)):
            order = range(1, len(files)+1)

        return ((idx, files[idx-1]) for idx in order)


    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    files = _get_uploads(request)

    # If user clicked on button but no files were uploaded
    if not files:
        return HttpResponseRedirect(reverse('uploads'))

    # Get options
    try:
        # make sure value is multiple of 90
        rotate = int(request.POST.get('rotate', '0')) / 90 * 90
    except ValueError:
        rotate = 0
    try:
        # make sure value is multiple of 90
        pages_sheet = int(request.POST.get('pages_sheet', '1'))
        if not pages_sheet in (1, 2, 4, 6, 9, 16):
            raise ValueError
    except ValueError:
        pages_sheet = 1

    text_overlay = request.POST.get('text_overlay', None)
    if text_overlay:
        overlay = get_overlay_page(text_overlay)
    else:
        overlay = None

    output = PdfFileWriter()

    # Get pdf objects and arrange in the user selected order, then parse ranges
    order = request.POST.get('order', "")
    for item_idx, file_obj in order_files(files, order):
        file_obj.file.open('r')
        pdf_obj = PdfFileReader(file_obj.file)
        page_count = pdf_obj.getNumPages()

        # Get page ranges
        pages = request.POST.get('pages_%d' % item_idx, "")
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
        if rotate:
            map(lambda page: page.rotateClockwise(rotate), pages)
        if overlay:
            map(lambda page: page.mergePage(overlay), pages)

        map(output.addPage, pages)

    # TODO get proper file name
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=combined.pdf'

    output.write(response)

    return response
