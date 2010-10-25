import os
import tempfile

from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from sqlalchemy.orm.interfaces import MapperExtension
from sqlalchemy.orm.exc import NoResultFound

from pdfserver.database import metadata, db_session
from pdfserver import app

class Upload(object):
    query = db_session.query_property()

    def __init__(self, localpath=None, filename=None, page_count=None):
        self.localpath = localpath
        self.filename = filename
        self.page_count = page_count

    def __repr__(self):
        return '<Upload %r, %r>' % (self.filename, self.file_path)

    @classmethod
    def get_for_id(cls, id):
        app.logger.debug("Getting file %r" % id)
        try:
            return cls.query.filter(cls.id == id).one()
        except NoResultFound:
            return None

    @classmethod
    def get_for_ids(cls, id_list):
        app.logger.debug("Getting files %r" % (id_list, ))
        return cls.query.filter(cls.id.in_(id_list)).all()

    @classmethod
    def add(cls, upload):
        db_session.add(upload)

    @classmethod
    def delete(cls, upload):
        db_session.delete(upload)

    @classmethod
    def commit(cls):
        db_session.commit()

    def store_file(self, file):
        self.filename = file.filename
        f, self.localpath = tempfile.mkstemp(dir=app.config['UPLOAD_TO'])
        app.logger.debug("Storing upload to %s" % self.file_path)
        file.save(self.file_path)

        # save pdf page count
        try:
            f = self.get_file()
            from pyPdf import PdfFileReader
            pdf_obj = PdfFileReader(f)
            self.page_count = pdf_obj.getNumPages()
            app.logger.debug("Read %d pages" % self.page_count)
            f.close()
        except Exception, e:
            pass

    def get_file(self):
        path = self.file_path
        if not path:
            return None

        return open(path, 'rb')

    def delete_file(self):
        os.remove(self.file_path)

    @property
    def file_path(self):
        return os.path.join(app.config['UPLOAD_TO'], self.localpath)

    @property
    def size(self):
        if self.localpath:
            return os.path.getsize(self.file_path)


class DeleteFileExtension(MapperExtension):
    def after_delete(self, mapper, connection, instance):
        instance.delete_file()


uploads = Table('uploads', metadata,
    Column('id', Integer, primary_key=True),
    Column('localpath', String(255), unique=True),
    Column('filename', String(255)),
    Column('page_count', Integer),
    # Use AUTOINCREMENT for sqlite3 to yield globally unique ids
    #   -> new ids cannot take on ids of deleted items, security issue!
    sqlite_autoincrement=True,
)

mapper(Upload, uploads, extension=DeleteFileExtension())
