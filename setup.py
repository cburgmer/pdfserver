import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "django-pdfserver",
    version = "0.2.1",
    packages = ['pdfserver'],
    author = "Christoph Burgmer",
    author_email = "cburgmer@ira.uka.de",
    description = "Pdfserver is a webservice that offers common PDF operations like joining documents or selecting pages.",
    long_description=open('README').read(),
    url = "http://cburgmer.nfshost.com/pdfserver/",
    package_data = {'pdfserver': ['templates/*.html', 'locale/*/*.mo', 'locale/*/*.po',
                                  'media/css/*.css', 'media/css/images/*','media/js/*.js']},
    install_requires=['pyPdf >= 1.12', 'Django >= 1.0'],
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
