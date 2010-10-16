import re

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            # TODO support version numbers
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements

def parse_dependency_links(file_name):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    return dependency_links


setup(
    name = "pdfserver",
    version = "0.3",
    packages = ['pdfserver'],
    author = "Christoph Burgmer",
    author_email = "cburgmer@ira.uka.de",
    description = 'Pdfserver is a webservice that offers common PDF operations like joining documents, selecting pages or "n pages on one".',
    long_description=open('README.rst').read(),
    url = "http://cburgmer.nfshost.com/pdfserver/",
    package_data = {'pdfserver': ['templates/*.html', 'locale/*/*.mo',
                                  'locale/*/*.po', 'media/css/*.css',
                                  'media/css/images/*','media/js/*.js']},
    install_requires = parse_requirements('requirements.txt'),
    dependency_links = parse_dependency_links('requirements.txt'),
    #extras_require = {
    #    'async': ['celery'],
    #},
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
