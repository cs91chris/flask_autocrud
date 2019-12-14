"""
Flask-AutoCRUD
-------------

Automatically generated a RESTful API services for CRUD operation and queries on database
"""
import sys
import pytest

from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test

from flask_autocrud import __version__
from flask_autocrud import __author_info__


with open("README.rst") as fh:
    long_description = fh.read()


class PyTest(test):
    def finalize_options(self):
        """

        """
        test.finalize_options(self)

    def run_tests(self):
        """

        """
        sys.exit(pytest.main(['tests']))


setup(
    name='Flask-AutoCRUD',
    version=__version__,
    url='https://github.com/cs91chris/flask_autocrud/',
    license='MIT',
    author=__author_info__['name'],
    author_email=__author_info__['email'],
    description='Automatically generated a RESTful API services for CRUD operation and queries on database',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'autocrud = flask_autocrud.scripts.run:main',
        ],
    },
    tests_require=[
        'pytest==4.5.0',
        'pytest-cov==2.7.1'
    ],
    install_requires=[
        'Flask==1.1.*',
        'Flask-SQLAlchemy==2.4.*',
        'Flask-ResponseBuilder==2.*',
        'Flask-ErrorsHandler==2.*',
        'sqlalchemy-filters==0.10.*',
        'colander==1.7.*',
        'PyYAML==5.*'
    ],
    cmdclass={'test': PyTest},
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
