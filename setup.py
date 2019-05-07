"""
Flask-AutoCRUD
-------------

Automatically generated a RESTful API services for CRUD operation and queries on database
"""

from setuptools import setup
from setuptools import find_packages

from flask_autocrud import __version__
from flask_autocrud import __author__

author, email = __author__.split()
email = email.lstrip('<').rstrip('>')

with open("README.rst", "r") as fh:
    long_description = fh.read()


setup(
    name='Flask-AutoCRUD',
    version=__version__,
    url='https://github.com/cs91chris/flask_autocrud/',
    license='MIT',
    author=author,
    author_email=email,
    description='Automatically generated a RESTful API services for CRUD operation and queries on database',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask==1.0.2',
        'Flask-SQLAlchemy==2.4.0',
        'Flask-ResponseBuilder==2.0.1',
        'sqlalchemy-filters==0.10.0'
    ],
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
