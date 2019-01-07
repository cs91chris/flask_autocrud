Flask-AutoCRUD
==============

Based on `sandman2 <https://github.com/jeffknupp/sandman2>`__.

Automatically generate a RESTful API service for CRUD operation on
database. If a list of tables or a list of sqlalchemy model is not
provided, all tables are affected.

For api documentation see `sandman2
documentation <http://sandman2.readthedocs.io/en/latest/>`__

Quickstart
~~~~~~~~~~

Install ``flask_autocrud`` using ``pip``:

::

   $ pip install Flask-AutoCRUD

.. _section-1:

Example usage
^^^^^^^^^^^^^

.. code:: python

   from flask import Flask

   from flask_admin import Admin
   from flask_autocrud import AutoCrud
   from flask_sqlalchemy import SQLAlchemy


   app = Flask(__name__)
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///db.sqlite3'
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   app.config['AUTOCRUD_METADATA_ENABLED'] = False

   db = SQLAlchemy(app)
   admin = Admin(app, base_template='layout.html', template_mode='bootstrap3')
   AutoCrud(db, app, admin=admin)

   app.run(debug=True)

Go to http://127.0.0.1:5000/ and see all available resources with its
endpoint

.. _section-2:

Configuration
^^^^^^^^^^^^^

1. ``AUTOCRUD_METADATA_ENABLED``: *(default: True)* enable metadata
   endpoint for a resource: ``<endpoint>/<resource>/meta``
2. ``AUTOCRUD_READ_ONLY``: *(default: False)* enable only http GET
   method
3. ``AUTOCRUD_BASE_URL``: *(default: ‘/’)* prefix url for resources
4. ``AUTOCRUD_SUBDOMAIN``: *(default: None)* bind autocrud endpoints to
   a subdomain #

License MIT
