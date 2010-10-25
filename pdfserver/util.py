# -*- coding: utf-8 -*-

import re
import math
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from itertools import product
except ImportError:
    def product(*args):
        ans = [[]]
        for arg in args:
            ans = [x+[y] for x in ans for y in arg]
        return ans

from pyPdf import PdfFileWriter, PdfFileReader
from pyPdf.pdf import PageObject

from pdfserver import app

def handle_pdfs(files_handles, page_range_text=None, pages_sheet=1, rotate=0,
                overlay=None):
    """
    Does the actual work on the pdf files:

    * Merges
    * Selects page ranges
    * Joins n pages on one
    * Rotates
    * Adds watermark
    """
    output = PdfFileWriter()

    if overlay and isinstance(overlay, basestring):
        overlay = get_overlay_page(overlay)

    for item_idx, handle in enumerate(files_handles):
        f = handle.get_file()
        pdf_obj = PdfFileReader(f)
        page_count = pdf_obj.getNumPages()

        # Get page ranges
        page_ranges = []
        if (page_range_text and len(page_range_text) > item_idx
            and page_range_text[item_idx]):
            ranges = re.findall(r'\d+\s*-\s*\d*|\d*\s*-\s*\d+|\d+',
                                page_range_text[item_idx])
            for p_range in ranges:
                match_obj = re.match(r'^(\d*)\s*-\s*(\d*)$', p_range)
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
                    page_idx = int(p_range)-1
                    if page_idx >= 0 and page_idx < page_count:
                        page_ranges.append([page_idx])
        else:
            page_ranges = [range(page_count)]

        # Extract pages from PDF
        pages = []
        for page_range in page_ranges:
            for page_idx in page_range:
                pages.append(pdf_obj.getPage(page_idx))

        # Apply operations
        if pages_sheet > 1 and pages:
            if hasattr(pages[0].mediaBox, 'getWidth'):
                pages = n_pages_on_one(pages, pages_sheet)
            else:
                app.logger.debug("pyPdf too old, not merging pages onto one")
        if rotate:
            app.logger.debug("rotate, clockwise, %r " % rotate)
            map(lambda page: page.rotateClockwise(rotate), pages)
        if overlay:
            map(lambda page: page.mergePage(overlay), pages)
        # Compress
        map(lambda page: page.compressContentStreams(), pages)

        map(output.addPage, pages)

    buffer = StringIO()
    output.write(buffer)
    return buffer.getvalue()

def lower_divisor_iterator(value):
    """
    Iterates over all divisors of the given value smaller or equal to the
    value's square root in decreasing order.
    """
    i = int(math.sqrt(value))
    while i > 0:
        if value % i == 0:
            yield i
        i -= 1

def _get_rotation_scaling(width, height, cell_x_count, cell_y_count):
    """
    Calculate rotaion and scaling factor for best useage of target page, i.e.
    largest possible scaling factor for least scaling.
    """
    # 1. Check no rotation
    plain_scaling_factor = min(1. / cell_x_count, 1. / cell_y_count)
    # 2. Check rotation by 90°
    #   (Example: Page XXXX would at best yield AABB for 2 pages on 1 sheet,
    #                  XXXX                     AABB
    #    i.e. the original width needs to hold 2 x the sheet's height, and
    #         the original height holds 1/2 x the sheet's width)
    rotate_scaling_factor = min(1. * width / (cell_x_count * height),
                                1. * height / (cell_y_count * width))

    if rotate_scaling_factor > plain_scaling_factor:
        return 90, rotate_scaling_factor
    else:
        return 0, plain_scaling_factor

def _get_optimal_placement(width, height, page_count):
    """
    Calculates the optimal placement on a sheet for the given number of pages.

    Estimates:
        - Rotation (0° / 90°)
        - Scaling factor (< 1)
        - Cell structure (width x height)
    """
    rotation = scaling_factor = None
    cell_x_count = cell_y_count = None

    # Check all possible decompositions
    # TODO don't start at square root, as that would asume next to quadratic
    #   layout of the page, choose a decomposition next to the page's ratio
    for lower_divisor in lower_divisor_iterator(page_count):
        higher_divisor = page_count / lower_divisor

        # Check A x B with A < B
        rot1, scal1 = _get_rotation_scaling(width, height,
                                            lower_divisor, higher_divisor)
        # Check B x A with A < B
        rot2, scal2 = _get_rotation_scaling(width, height,
                                            higher_divisor, lower_divisor)

        scal, rot, x, y = max((scal1, rot1, lower_divisor, higher_divisor),
                              (scal2, rot2, higher_divisor, lower_divisor))

        if scaling_factor is None or scaling_factor < scal:
            scaling_factor = scal
            rotation = rot
            cell_x_count = x
            cell_y_count = y
        else:
            # Once the scaling factor decreases in both directions we won't get
            #   any better
            break

    return rotation, scaling_factor, cell_x_count, cell_y_count

def n_pages_on_one(pages, pages_sheet):
    width = float(pages[0].mediaBox.getWidth())
    height = float(pages[0].mediaBox.getHeight())

    # Calculate placement parameters
    rotation, scaling, cell_x_count, cell_y_count = _get_optimal_placement(
        width, height, pages_sheet)

    # Get placement matrix, ajust to rotation
    if rotation:
        # From down to up, left to right
        # Also ajust to "one-off issue"
        placement = list(product(range(1, cell_x_count+1),
                                 range(cell_y_count-1, -1, -1)))
    else:
        # From left to right, up to down
        placement = map(lambda (x, y): (y, x),
                        list(product(range(cell_y_count),
                                     range(cell_x_count))))

    new_pages = []

    # Merge pages
    for new_page_idx in range(int(math.ceil(1. * len(pages) / pages_sheet))):
        offset = new_page_idx * pages_sheet
        # Start from blank page
        new_page = PageObject.createBlankPage(None, width, height)

        # Get `pages_sheet` number of pages and merge together
        for idx, page in enumerate(pages[offset:offset+pages_sheet]):
            x, y = placement[idx]

            # Get coordinates
            w = width * x / cell_x_count
            h = height * (y+1) / cell_y_count
            # TODO align page so that it takes the center of its cell
            new_page.mergeRotatedScaledTranslatedPage(page,
                                                      rotation, scaling,
                                                      w, height-h)

        new_pages.append(new_page)

    return new_pages

def write_text_overlay(text):
    """
    Writes a PDF file with the given text to be used as an "overlay".
    """
    try:
        from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
        from reportlab.lib import styles, enums, colors, units
    except ImportError:
        app.logger.debug("No report lab found, not generating text overlay")
        return None

    styles = styles.getSampleStyleSheet()
    style = styles["Normal"]
    style.fontSize = 100
    style.leading = 110
    style.alignment = enums.TA_CENTER
    gray = colors.slategrey
    gray.alpha = 0.5
    style.textColor = gray

    f = StringIO()
    doc = SimpleDocTemplate(f)
    doc.build([Spacer(1, 3.5 * units.inch), Paragraph(text, style)])

    return f

def get_overlay_page(text_overlay):
    try:
        # Write pdf overlay with reportpdf
        f = write_text_overlay(text_overlay)

        # Get page object
        overlay_pdf = PdfFileReader(f)
        overlay = overlay_pdf.getPage(0)

        return overlay
    except Exception, e:
        app.logger.debug("IOError generating text overlay: %s" % e)
        pass


from functools import wraps
from flask import render_template

# from http://flask.pocoo.org/docs/patterns/viewdecorators/#templating-decorator
def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator
