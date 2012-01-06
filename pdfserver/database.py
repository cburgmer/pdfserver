from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

from pdfserver import app

app.logger.debug("Using database %r" % app.config['DATABASE'])
engine = create_engine(app.config['DATABASE'], convert_unicode=True)
metadata = MetaData()
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

app.dbhook = lambda: db_session.remove()

def init_db():
    metadata.create_all(bind=engine)
