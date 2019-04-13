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

   from flask_autocrud import AutoCrud
   from flask_sqlalchemy import SQLAlchemy


   app = Flask(__name__)
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///db.sqlite3'
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   app.config['AUTOCRUD_METADATA_ENABLED'] = True

   db = SQLAlchemy(app)
   AutoCrud(app, db)

   app.run(debug=True)

Go to http://127.0.0.1:5000/ and see all available resources with its
endpoint. NOTE: you must set SQLALCHEMY_DATABASE_URI with your database.

If you want to see an example use with Flask-Admin see in example folder.

.. _section-2:

Filtering and Sorting
^^^^^^^^^^^^^^^^^^^^^

Add filters as query string parameters, they are used in AND.
    - null value: ``null``
    - in operator: list separated by ``;``
    - not operator: ``!`` means: not equal, not null, not in
    - like operator: ``%`` for example: %%test%, %test% or %%test.
      NOTE first % are not used in expression, it only indicated that value must be used with like operator.

NOTE: At this time OR operator are not implemented

Use ``fields`` parameter to get only the fields listes as value, separated by ``;``.

Use ``export`` parameter to export data into csv format.

Sorting is implemented with ``sort`` parameter. The value is a list of field separated by `;`
You can prepend ``-`` to reverse order.

.. _section-3:

Configuration
^^^^^^^^^^^^^

1. ``AUTOCRUD_METADATA_ENABLED``: *(default: True)* enable metadata
   endpoint for a resource: ``<endpoint>/<resource>/meta``
2. ``AUTOCRUD_READ_ONLY``: *(default: False)* enable only http GET
   method
3. ``AUTOCRUD_BASE_URL``: *(default: '/')* prefix url for resources
4. ``AUTOCRUD_SUBDOMAIN``: *(default: None)* bind autocrud endpoints to
   a subdomain

License MIT
