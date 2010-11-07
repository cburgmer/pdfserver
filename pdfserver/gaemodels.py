import sys
from StringIO import StringIO

from google.appengine.ext import db

from pdfserver import app

MAX_BLOB_SIZE = 1000000 # ~1 MB, works for me

USE_1MB_WORKAROUND = True
"""
The Google App Engine can only host datastore entries with max 1MB size. By
slicing a file into several pieces, we can circumvent this and instead store
BLOB_COUNT * MAX_BLOB_SIZE bytes.
"""

class Upload(db.Model):
    filename = db.TextProperty()
    page_count = db.IntegerProperty()
    file_blob = db.BlobProperty()

    def __repr__(self):
        return '<Upload %r>' % self.filename

    @property
    def id(self):
        return self.key().id()

    @classmethod
    def get_for_id(cls, id):
        return cls.get_by_id(id)

    @classmethod
    def get_for_ids(cls, id_list):
        result = cls.get_by_id(id_list)
        if result is None:
            return []
        else:
            # Keys are never deleted, will return a None type
            return [obj for obj in result if obj is not None]

    @classmethod
    def add(cls, upload):
        key = upload.put()
        if USE_1MB_WORKAROUND:
            try:
                cls.store_unsaved_content(upload)
            except ValueError:
                cls.delete(upload)
                raise

    @classmethod
    def delete(cls, upload):
        db.delete([upload])
        if USE_1MB_WORKAROUND:
            blobs = []
            for i in range(BLOB_COUNT):
                blob_cls = getattr(sys.modules[__name__], 'FileBlob%d' % i)
                blob = blob_cls.all().filter('upload =', upload).get()
                if blob:
                    blobs.append(blob)
            db.delete(blobs)

    @classmethod
    def commit(cls):
        pass

    @classmethod
    def store_unsaved_content(cls, upload):
        upload.unsaved_content.seek(0)
        for i in range(BLOB_COUNT):
            app.logger.debug("Cheating AppEngine, storing blob slices...")
            blob_cls = getattr(sys.modules[__name__], 'FileBlob%d' % i)
            blob = blob_cls(upload=upload,
                            blob=db.Blob(upload.unsaved_content.read(
                                                                MAX_BLOB_SIZE)))
            blob.put()
        if len(upload.unsaved_content.read(1)) > 0:
            raise ValueError("Uploaded file too big")

    def store_file(self, file):
        self.filename = file.filename
        app.logger.debug("Storing upload from %s" % self.filename)
        buf = StringIO(file.read())

        if USE_1MB_WORKAROUND:
            self.unsaved_content = buf
        else:
            self.file_blob = db.Blob(buf)

        # save pdf page count
        try:
            from pyPdf import PdfFileReader
            pdf_obj = PdfFileReader(buf)
            self.page_count = pdf_obj.getNumPages()
            app.logger.debug("Read %d pages" % self.page_count)
        except Exception, e:
            app.logger.debug("Exception getting page count: %r" % e)
            pass

    def get_file(self):
        buf = StringIO()
        if USE_1MB_WORKAROUND:
            for i in range(BLOB_COUNT):
                blob_cls = getattr(sys.modules[__name__], 'FileBlob%d' % i)
                blob = blob_cls.all().filter('upload =', self).get().blob
                buf.write(blob)
        else:
            buf.write(self.file_blob)

        return buf

    @property
    def size(self):
        if USE_1MB_WORKAROUND:
            blob_size = 0
            for i in range(BLOB_COUNT):
                blob_cls = getattr(sys.modules[__name__], 'FileBlob%d' % i)
                blob = blob_cls.all().filter('upload =', self).get()
                if blob:
                    blob_size += len(blob.blob)
            return blob_size
        else:
            return len(self.file_blob)


class FileBlob0(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob1(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob2(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob3(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob4(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob5(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob6(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob7(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob8(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

class FileBlob9(db.Model):
    upload = db.ReferenceProperty(Upload)
    blob = db.BlobProperty()

BLOB_COUNT = 10

if USE_1MB_WORKAROUND:
    max_upload_bytes = BLOB_COUNT * MAX_BLOB_SIZE
else:
    max_upload_bytes = MAX_BLOB_SIZE

if (not app.config['MAX_CONTENT_LENGTH']
    or app.config['MAX_CONTENT_LENGTH'] > max_upload_bytes):
    app.logger.info("No MAX_CONTENT_LENGTH set, or value to high. "
                    "Reset to %d bytes." % max_upload_bytes)
    app.config['MAX_CONTENT_LENGTH'] = max_upload_bytes
