"""
Flask-AutoCRUD
-------------

Automatically generated a RESTful API services for CRUD operation and queries on database
"""
import os
import re
import sys

from setuptools.command.test import test
from setuptools import setup, find_packages

BASE_PATH = os.path.dirname(__file__)
VERSION_FILE = os.path.join('flask_autocrud', 'version.py')


def read(file):
    """

    :param file:
    :return:
    """
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    """

    :param file:
    :param name:
    :return:
    """
    pattern = r"{attr}\W*=\W*'([^']+)'".format(attr=name)
    value, = re.findall(pattern, read(file))
    return value


def readme(file):
    """

    :param file:
    :return:
    """
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)


class PyTest(test):
    def finalize_options(self):
        """

        """
        test.finalize_options(self)

    def run_tests(self):
        """

        """
        import pytest
        sys.exit(pytest.main(['tests']))


setup(
    license='MIT',
    name='Flask-AutoCRUD',
    url='https://github.com/cs91chris/flask_autocrud/',
    version=grep(VERSION_FILE, '__version__'),
    author=grep(VERSION_FILE, '__author_name__'),
    author_email=grep(VERSION_FILE, '__author_email__'),
    description='Automatically generated a RESTful API services for CRUD operation and queries on database',
    long_description=readme('README.rst'),
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
        'pytest >= 5',
        'pytest-cov >= 2'
    ],
    install_requires=[
        'Flask >= 1.0.4',
        'Flask-SQLAlchemy >= 2.4',
        'Flask-ResponseBuilder >= 2.0.9',
        'Flask-ErrorsHandler >= 3',
        'sqlalchemy-filters >= 0.11',
        'colander >= 1.7',
        'PyYAML'
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
