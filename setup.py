import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "django-pdfserver",
    version = "0.1",
    packages = ['pdfserver'],
    author = "Christoph Burgmer",
    author_email = "cburgmer@ira.uka.de",
    description = "A Django application that offers basic PDF operations as a webservice.",
    long_description=open('README').read(),
    url = "http://cburgmer.nfshost.com/pdfserver/",
    package_data = {'pdfserver': ['templates/*.html', 'locale/*/*.mo', 'locale/*/*.po',
                                  'media/css/*.css', 'media/css/images/*','media/js/*.js']},
    classifiers = [
    	"Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    	],
)
