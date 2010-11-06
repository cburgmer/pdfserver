import unittest
import os
import re
import difflib
import random
from StringIO import StringIO

import werkzeug
from flask import session

from pyPdf import PdfFileReader, PdfFileWriter

import pdfserver

TEST_PDF = """
eJyNVW1z2kYQ/s4M/+HGMQWmAb0hEC5xzWtMDZiAaEoskh7SAXJBR0+n2O5M+wfab/3e39o9CQkF
0pniAZ/29p599tndU27c6ZWUciWbyf3915//oAnZU8YHeIneEo8wzImDwAU51A52xONow/n+SpKe
np7KLPTd4mXZpjsAQPkW9l27Rz3u56+QvcW+Lw53XJu71MPsBWUzCpIRXT4Kd3NDkM+x52DmoJU4
hZzENZtpNJDUU5AKBybo+jqbIZ5zOJnvKekA5sueKCIs4KtH/NByS7afCXdtHAECQxLapdQGkrqe
TR3XWyPpves1Pd+NDWJzhHdEUBHrabDkEA1JYUxhMcPHEPOE5BivyRc8hQEoakeKoeU06TZgEaFG
TaQuYgyJ4+IWfUYPSIZn8dXrelmt6VVYGhWlbBh1Ay2E7xgzUadqfHZCfBowm/goFFTwVOK9MaP2
lHCAlYBemA155uJ/fwfMWsmqnaz6aBHmCcCUQ3uEZCSTYS8McNiLRAmzOxFlUkkr0sYcb+kaRKkc
RenEvTahlEeS3Ad863qQg5FQB+whdSDKzCcj6pHY6B9Tj1jEMU6J6GkifW9FgYUesxBBmwHfUIYK
VgF71HvZ0cC3ikUB3GYEi5J1hACFzpUqK/CnVhRdUXStJCt5Wc4fPSOQwPP3xHZXLnEOMHfk5Yky
x0eF4qEaTmATcD5OoZi9gbtkYnhK6GzqioeefCQ2/3oM0+VbcprDmRbV0zb1QYzqsSR7UUnOCIk7
NBBtFObgAv8HpIVTuviy9v5ZnFo6zhQA8Q4C1U4C+eHG4QZwtxwkgQ5tTtv9vqF3CExmWO3eFuSP
HqPIA+Kt+QYpuhwGjmHe4v27jdx903stz6xbzbT2o7n58d3dL99z+7o/fv3d+1cz5aOquZtxd/jJ
HPuvljcD9qE9pJtJW/HH85urxuOINO9uu4Nloz9u0TI1jVVDmg1nt471Q5ONe51LY2Je4v6vP7Z3
weVPElvylju/4Nf3bz4UfOlB03o33yjm4sI09Ytv5z//cQ2yxATTChlphZK2z2aMdGdG+stHtRPH
tODPjKyyGRnV4Sf5oKquazpaJTZFgdqFO15iU+X6mU2rqWe2auXcr2ac4SmyfnYWBqV2Zquk8TjD
7pawKON+BzRAudT7af3191OpBPcptB6Mw3+9qooC6qFgadWKVbS0SvV3C0bXKiqSJavayNJU+fN8
aKmaboEURfS/PRcAHF6U4jLRkwsYbjFUiZ+m7m8E1Q/9iRmPigQtC9XM5br3cAv/Cx4sEhw=
"""
"""Test PDF file, zlib and base64 encoded."""

class PdfserverTestCase(unittest.TestCase):

    def get_pdf_stream(self):
        return StringIO(TEST_PDF.replace('\n', '')\
                                .decode('base64')\
                                .decode('zlib'))

    def extract_ids_from_main_page(self, data):
        ids = re.findall(r'<tr class="(?:[^"]+ )?file(?: [^"]+)?" '
                         r'id="file_(\d+)">',
                         data)
        return map(int, ids)

    def clean_up(self):
        from pdfserver.models import Upload
        for upload in Upload.query.all():
            Upload.delete(upload)
        Upload.commit()

    def setUp(self):
        pdfserver.app.config['DATABASE'] = 'sqlite://'
        pdfserver.app.config['SECRET_KEY'] = 'test key'
        pdfserver.app.config['UPLOAD_TO'] = '/tmp'
        #pdfserver.app.config['DEBUG'] = True
        pdfserver.app.config['TASK_HANDLER'] = 'pdfserver.faketask'

        self.app = pdfserver.app.test_client()
        from pdfserver import models, faketask, database
        database.init_db()

    def tearDown(self):
        self.clean_up()


class UploadTestCase(PdfserverTestCase):

    def test_upload_returns_redirect(self):
        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        self.assertEquals(rv.status_code, 302)

        self.clean_up()

    def test_upload_shows_resulting_file(self):
        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')},
                           follow_redirects=True)

        self.assert_('test.pdf' in rv.data)

        self.clean_up()

    def test_upload_creates_file(self):
        from pdfserver.models import Upload

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        upload = Upload.query.filter(Upload.filename == 'test.pdf').one()
        os.path.exists(upload.file_path)

        self.clean_up()

    def test_upload_creates_database_entry(self):
        from pdfserver.models import Upload

        assert Upload.query.count() == 0

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        self.assertEquals(Upload.query.count(), 1)

        self.clean_up()

    def test_upload_yields_correct_file_ids(self):
        from pdfserver.models import Upload

        assert Upload.query.count() == 0

        with self.app as c:
            rv = c.post('/handleform',
                        data={'file': (self.get_pdf_stream(), 'test.pdf')},
                        follow_redirects=True)
            rv = c.post('/handleform',
                        data={'file': (self.get_pdf_stream(), 'test2.pdf')},
                        follow_redirects=True)
            rv = c.post('/handleform',
                        data={'file': (self.get_pdf_stream(), 'test3.pdf')},
                        follow_redirects=True)

            # Get file ids
            ids = self.extract_ids_from_main_page(rv.data)
            self.assertEquals(sorted(ids), sorted(session['file_ids']))

            self.assertEquals(Upload.query.filter(Upload.id.in_(ids)).count(),
                              3)

        self.clean_up()


class DeleteTestCase(PdfserverTestCase):

    def test_remove_removes_upload(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')},
                           follow_redirects=True)

        # Get file id
        ids = self.extract_ids_from_main_page(rv.data)
        self.assert_(len(ids) == 1)

        rv = self.app.post('/delete',
                           data={'id': ids[0]},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        self.assertEquals(Upload.query.count(), 0)

    def test_remove_all(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        self.app.post('/handleform',
                      data={'file': (self.get_pdf_stream(), 'test.pdf')})
        self.app.post('/handleform',
                      data={'file': (self.get_pdf_stream(), 'test2.pdf')})

        self.assertEquals(Upload.query.count(), 2)

        rv = self.app.post('/handleform',
                           data={'form_action': 'deleteall'},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        self.assertEquals(Upload.query.count(), 0)

    def test_remove_does_not_affect_others(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')},
                           follow_redirects=True)

        # Get file id first upload
        ids = self.extract_ids_from_main_page(rv.data)
        self.assert_(len(ids) == 1)

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test2.pdf')},
                           follow_redirects=True)
        # Get file id second upload
        ids2 = self.extract_ids_from_main_page(rv.data)
        ids2.remove(ids[0])
        self.assert_(len(ids2) == 1)

        self.assertEquals(Upload.query.count(), 2)

        # Delete first file
        rv = self.app.post('/delete',
                           data={'delete': 'delete', 'id': ids[0]},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        # Make sure second file still exists
        self.assertEquals(Upload.query.count(), 1)
        self.assert_(Upload.get_for_id(ids2[0]) is not None)

        self.clean_up()

    def test_delete_non_existant_fails(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        rv = self.app.post('/delete',
                           data={'delete': 'delete', 'id': '1'},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 404)

    def test_confirm_delete_cancel_has_no_effect(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        self.app.post('/handleform',
                      data={'file': (self.get_pdf_stream(), 'test.pdf')})

        self.assertEquals(Upload.query.count(), 1)

        rv = self.app.post('/handleform',
                           data={'form_action': 'cancel'},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        self.assertEquals(Upload.query.count(), 1)

        self.clean_up()


class InteractionTestCase(PdfserverTestCase):

    def setUp(self):
        PdfserverTestCase.setUp(self)
        self.app2 = pdfserver.app.test_client()

    def test_two_client_interaction(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        self.app.post('/handleform',
                      data={'file': (self.get_pdf_stream(), 'test.pdf')})
        ids = [upload.id for upload in Upload.query.all()]
        self.assertEquals(len(ids), 1)
        app_id = ids[0]

        self.app2.post('/handleform',
                       data={'file': (self.get_pdf_stream(), 'test.pdf')})
        ids = [upload.id for upload in Upload.query.all()
                         if upload.id != app_id]
        self.assertEquals(len(ids), 1)
        app2_id = ids[0]

        self.assert_(app_id != app2_id)

        # Get file id for app 1
        rv = self.app.get('/')
        ids = self.extract_ids_from_main_page(rv.data)
        self.assertEquals(ids, [app_id])

        # Get file id for app 2
        rv = self.app2.get('/')
        ids = self.extract_ids_from_main_page(rv.data)
        self.assertEquals(ids, [app2_id])

        self.clean_up()

    def test_remove_upload_from_other_client_fails(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0

        self.app.post('/handleform',
                      data={'file': (self.get_pdf_stream(), 'test.pdf')})
        ids = [upload.id for upload in Upload.query.all()]
        self.assertEquals(len(ids), 1)
        app_id = ids[0]

        self.app2.post('/handleform',
                       data={'file': (self.get_pdf_stream(), 'test.pdf')})

        # Delete upload from app1 in app2
        rv = self.app2.post('/delete',
                            data={'delete': 'delete', 'id': app_id},
                            follow_redirects=True)

        # Check for 404 file not found
        #   (we don't reveal that there actually is a file)
        self.assertEquals(rv.status_code, 404)

        self.assertEquals(Upload.query.count(), 2)

        self.clean_up()


class DownloadMixin(object):

    def clean_up(self):
        super(DownloadMixin, self).clean_up()

        from pdfserver.faketask import TaskResult
        TaskResult.query.delete()
        TaskResult.commit()

    def combine_and_download(self, **data):
        options = {'form_action': 'combine'}
        options.update(data)
        # Start build
        rv = self.app.post('/handleform',
                           data=options,
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        # Fetch download link
        match = re.search('"(/download/[^/"]+)"', rv.data)
        self.assert_(match is not None)

        # Download
        rv = self.app.get(match.group(1))
        self.assertEquals(rv.status_code, 200)

        return rv


class DownloadTestCase(DownloadMixin, PdfserverTestCase):

    def test_build_result_is_downloadable(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        rv = self.combine_and_download()

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assert_('Test' in pdf_download.getPage(0).extractText())

        self.clean_up()

    def test_download_non_existant_fails(self):
        from pdfserver.models import Upload
        assert Upload.query.count() == 0
        from pdfserver.faketask import TaskResult
        assert TaskResult.query.count() == 0

        rv = self.app.get('/download/1')

        self.assertEquals(rv.status_code, 404)

        self.clean_up()

    def test_download_removed_fails(self):
        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        # Start build
        rv = self.app.post('/handleform', data={'form_action': 'combine'},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        # Fetch download link
        match = re.search('"(/download/([^/"]+))"', rv.data)
        self.assert_(match is not None)
        download_url = match.group(1)
        id = match.group(2)

        # Remove download
        rv = self.app.post('/removedownload',
                           data={'task_id': id},
                           follow_redirects=True)
        self.assertEquals(rv.status_code, 200)

        # Download
        rv = self.app.get(download_url)
        self.assertEquals(rv.status_code, 404)

        self.clean_up()

    def test_download_expired_fails(self):
        from pdfserver.faketask import TaskResult
        assert TaskResult.query.count() == 0

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        # Start build
        rv = self.app.post('/handleform', data={'form_action': 'combine'},
                           follow_redirects=True)

        self.assertEquals(rv.status_code, 200)

        # Fetch download link
        match = re.search('"(/download/([^/"]+))"', rv.data)
        self.assert_(match is not None)
        download_url = match.group(1)
        id = match.group(2)

        task_result = TaskResult.get_for_task_id(id)
        task_result.available = False
        TaskResult.add(task_result)

        # Download
        rv = self.app.get(download_url)
        self.assertEquals(rv.status_code, 410)

        self.clean_up()


class CombineTestCase(DownloadMixin, PdfserverTestCase):

    @classmethod
    def replace_text(cls, page, text, replace):
        # HACK
        from pyPdf.pdf import ContentStream, PageObject
        from pyPdf.generic import TextStringObject, NameObject
        content = ContentStream(page["/Contents"].getObject(), page.pdf)
        for idx in range(len(content.operations)):
            operands, operator = content.operations[idx]
            if operator == 'Tj':
                operands[0] = TextStringObject(operands[0].replace(text,
                                                                   replace))
        new_page = PageObject.createBlankPage(page.pdf)
        new_page.mergePage(page)
        new_page[NameObject('/Contents')] = content
        return new_page

    @classmethod
    def clone_document(cls, pdf, text, replace):
        output = PdfFileWriter()
        for page_idx in range(pdf.getNumPages()):
            page = pdf.getPage(page_idx)
            new_page = cls.replace_text(page, text, replace)
            output.addPage(new_page)
        return output

    def test_page_ranges(self):
        pdf = PdfFileReader(self.get_pdf_stream())

        # Build a document with twenty pages
        output = PdfFileWriter()
        page = pdf.getPage(0)
        for i in range(1, 21):
            new_page = CombineTestCase.replace_text(page, 'Test', 'Test %d' % i)
            output.addPage(new_page)
        assert output.getNumPages() == 20

        buf = StringIO()
        output.write(buf)
        buf.seek(0)

        rv = self.app.post('/handleform',
                           data={'file': (buf, 'test.pdf')},
                           follow_redirects=True)

        ids = self.extract_ids_from_main_page(rv.data)
        pages_kw = 'pages_%d' % ids[0]
        rv = self.combine_and_download(**{pages_kw: '-5, 10, 12-14, 18-'})

        pdf_download = PdfFileReader(StringIO(rv.data))

        # Test ranges
        ranges = [1, 2, 3, 4, 5, 10, 12, 13, 14, 18, 19, 20]

        self.assert_(all(
            (('Test %d' % page) in pdf_download.getPage(i).extractText())
                        for i, page in enumerate(ranges)))

        self.assertEquals(pdf_download.getNumPages(), len(ranges))

        self.clean_up()

    def test_file_order(self):
        pdf = PdfFileReader(self.get_pdf_stream())

        with self.app as c:
            # Upload 20 documents
            order = range(1, 20)
            for i in order:
                new_pdf = CombineTestCase.clone_document(pdf, 'Test',
                                                         'Test %d' % i)

                buf = StringIO()
                new_pdf.write(buf)
                buf.seek(0)

                c.post('/handleform', data={'file': (buf, 'test_%d.pdf' % i)})

            # Re-arrange uploads and download combined files
            random.shuffle(order)

            file_ids = session['file_ids']
            options = werkzeug.MultiDict([('file[]', i) for i in order]
                                        + [('upload_id_%d' % j, id)
                                            for j, id in enumerate(file_ids)])
            rv = self.combine_and_download(**options)

        pdf_download = PdfFileReader(StringIO(rv.data))

        # Test order
        self.assert_(all(
                    (('Test %d' % idx) in pdf_download.getPage(i).extractText())
                    for i, idx in enumerate(order)))

        self.assertEquals(pdf_download.getNumPages(), len(order))

        self.clean_up()


class WatermarkTestCase(DownloadMixin, PdfserverTestCase):

    def setUp(self):
        super(WatermarkTestCase, self).setUp()
        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

    def test_watermark(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()
        assert 'TEST_WATERMARK' not in pdf.getPage(0).extractText()

        rv = self.combine_and_download(text_overlay='TEST_WATERMARK')

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assert_('Test' in pdf_download.getPage(0).extractText())
        self.assert_('TEST_WATERMARK' in pdf_download.getPage(0).extractText())

        self.clean_up()


class RotationTestCase(DownloadMixin, PdfserverTestCase):

    def test_rotation_maintains_text(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        rv = self.combine_and_download(rotate='90')

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assert_('Test' in pdf_download.getPage(0).extractText())

        self.clean_up()

    def test_rotation_different_to_unrotated(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        # Start build without rotation
        rv = self.combine_and_download()
        content_no_rotation = rv.data

        # Start build with rotation
        rv = self.combine_and_download(rotate='180')
        content = rv.data

        self.assert_(content_no_rotation != content)

        self.clean_up()

    def test_rotation_identity(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        # Start build without rotation
        rv = self.combine_and_download(rotate='360')
        content_full = rv.data

        # Start build with rotation
        rv = self.combine_and_download(rotate='180')
        content_half = rv.data

        self.clean_up()

        # Upload rotated
        rv = self.app.post('/handleform',
                           data={'file': (StringIO(content_half), 'test.pdf')})

        # Start build with rotation
        rv = self.combine_and_download(rotate='180')
        content_two_half = rv.data

        self.assert_(content_two_half == content_full,
                     '\n'.join(difflib.ndiff(content_two_half.split('\n'),
                                             content_full.split('\n'))))

        self.clean_up()


class NPagesTestCase(DownloadMixin, PdfserverTestCase):

    def test_one_page(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()
        assert pdf.getNumPages() == 1

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        rv = self.combine_and_download(pages_sheet='2')

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assert_('Test' in pdf_download.getPage(0).extractText())
        self.assertEquals(pdf_download.getNumPages(), 1)

        self.clean_up()

    def test_two_on_one_page(self):
        # Build a document with two pages
        pdf = PdfFileReader(self.get_pdf_stream())
        output = PdfFileWriter()
        output.addPage(pdf.getPage(0))
        output.addPage(pdf.getPage(0))
        assert output.getNumPages() == 2
        assert output.getPage(0).extractText().count('Test') ==  1
        buf = StringIO()
        output.write(buf)
        buf.seek(0)

        rv = self.app.post('/handleform',
                           data={'file': (buf, 'test.pdf')})

        rv = self.combine_and_download(pages_sheet='2')

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assertEquals(pdf_download.getPage(0).extractText().count('Test'),
                          2)
        self.assertEquals(pdf_download.getNumPages(), 1)

        self.clean_up()

    def test_two_documents(self):
        # Make sure our Test string is available in the original document
        pdf = PdfFileReader(self.get_pdf_stream())
        assert 'Test' in pdf.getPage(0).extractText()
        assert pdf.getNumPages() == 1

        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})
        rv = self.app.post('/handleform',
                           data={'file': (self.get_pdf_stream(), 'test2.pdf')})

        rv = self.combine_and_download(pages_sheet='2')

        pdf_download = PdfFileReader(StringIO(rv.data))
        self.assert_('Test' in pdf_download.getPage(0).extractText())
        self.assertEquals(pdf_download.getNumPages(), 2)

        self.clean_up()


if __name__ == '__main__':
    unittest.main()
