"""
Flask-AutoCRUD
-------------

Automatically generate a RESTful API service for CRUD operation on database
"""
from setuptools import setup


with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='Flask-AutoCRUD',
    version='1.0',
    url='https://github.com/cs91chris/flask-autocrud/',
    license='MIT',
    author='cs91chris',
    author_email='cs91chris@voidbrain.me',
    description='Automatically generate a RESTful API service for CRUD operation on database',
    long_description=long_description,
    packages=['flask_autocrud'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask==1.0.2',
        'Flask-Admin==1.5.3',
        'Flask-SQLAlchemy==2.1',
        'Flask-JSON==0.3.3'
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
