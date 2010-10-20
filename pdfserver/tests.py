import unittest
import os
from StringIO import StringIO

import pdfserver

TEST_PDF = """
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
"""
"""Test PDF file, zlib and base64 encoded."""

class PdfserverTestCase(unittest.TestCase):

    def get_pdf_stream(self):
        return StringIO(TEST_PDF.replace('\n', '')\
                                .decode('base64')\
                                .decode('zlib'))

    def clean_up(self):
        from pdfserver.models import Upload
        for upload in Upload.query.all():
            Upload.delete(upload)

    def setUp(self):
        pdfserver.app.config['DATABASE'] = 'sqlite://'
        pdfserver.app.config['SECRET_KEY'] = 'test key'
        pdfserver.app.config['UPLOAD_TO'] = '/tmp'

        self.app = pdfserver.app.test_client()
        from pdfserver import models, faketask, database
        database.init_db()


class UploadTestCase(PdfserverTestCase):

    def test_upload_returns_redirect(self):
        file_stream = self.get_pdf_stream()
        rv = self.app.post('/upload',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        self.assertEquals(rv.status_code, 302)

        self.clean_up()

    def test_upload_shows_resulting_file(self):
        file_stream = StringIO(TEST_PDF.decode('base64').decode('zlib'))
        rv = self.app.post('/upload',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')},
                           follow_redirects=True)

        self.assert_('test.pdf' in rv.data)

        self.clean_up()

    def test_upload_creates_file(self):
        from pdfserver.models import Upload

        file_stream = StringIO(TEST_PDF.decode('base64').decode('zlib'))
        rv = self.app.post('/upload',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        upload = Upload.query.filter(Upload.filename == 'test.pdf').one()
        os.path.exists(upload.file_path)

        self.clean_up()

    def test_upload_creates_database_entry(self):
        from pdfserver.models import Upload

        self.assertEquals(Upload.query.count(), 0)

        file_stream = StringIO(TEST_PDF.decode('base64').decode('zlib'))
        rv = self.app.post('/upload',
                           data={'file': (self.get_pdf_stream(), 'test.pdf')})

        self.assertEquals(Upload.query.count(), 1)

        self.clean_up()



if __name__ == '__main__':
    unittest.main()
