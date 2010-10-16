from celery.decorators import task

from pdfserver.util import handle_pdfs

@task
def handle_pdfs_task(files_handles, page_range_text=None, pages_sheet=1,
                     rotate=0, overlay=None):
    output = handle_pdfs(files_handles, page_range_text=page_range_text,
                         pages_sheet=pages_sheet, rotate=rotate,
                         overlay=overlay)
    return output.encode('zlib')
