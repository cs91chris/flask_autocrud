Flask-AutoCRUD
==============

Inspired by `sandman2 <https://github.com/jeffknupp/sandman2>`__,
based on `sqlalchemy-filters <https://pypi.org/project/sqlalchemy-filters>`__
and `Flask-ResponseBuilder <https://pypi.org/project/Flask-ResponseBuilder>`__

Automatically generate a RESTful APIs for CRUD operation and advanced search on a database.
If a list of ``Model`` is not provided, all tables are affected, instead you can customize:

- resource name
- fields name
- resource url
- allowed methods
- hidden fields


Features
~~~~~~~~~~

- HATEOAS support
- conditional requests via ETag header
- full range of CRUD operations
- filtering, sorting and pagination
- customizable responses via query string
- custom FETCH method for advanced search
- JSON and XML response based on Accept header
- export to csv available
- meta resource description


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

Go to http://127.0.0.1:5000/resources and see all available resources with its
endpoint. NOTE: you must set SQLALCHEMY_DATABASE_URI with your database.

If you want to see an example use with Flask-Admin see in example folder.

.. _section-2:

Filtering and Sorting
^^^^^^^^^^^^^^^^^^^^^

Add filters as query string parameters, they are used in AND. NOTE: At this time OR operator are not implemented.

You can use entity fields as parameter with the following placeholders:

- null value: ``null``
- in operator: list separated by ``;``
- not operator: ``!`` means: not equal, not null, not in
- comparators: ``__gt__`` (grater), ``__lt__`` (lesser), ``__gte__`` (grater-equal), ``__lte__`` (lesser-equal)
- like operator: ``%`` for example: %%test%, %test% or %%test
  NOTE first % are not used in expression, it only indicated that value must be used with like operator.


Other parameters:

- Use ``_fields`` parameter to get only the fields listed as value, separated by ``;``.
- Use ``_limit`` and ``_page`` parameters for pagination.
- Sorting is implemented with ``_sort`` parameter. The value is a list of field separated by `;`
  You can prepend ``-`` to reverse order.
- Use ``_export`` parameter to export data into csv format.
- Use ``_extended`` in order to fetch data of related resources.
- Use ``_as_table`` in order to flatten nested dict useful if you want render response as table

Example requests:

- ``/invoice?InvoiceId=(35;344)``

- ``/invoice?Total=__lte__10&sort=Total``

- ``/invoice?fields=BillingCountry;Total;InvoiceId&InvoiceId=!355;344&sort=-InvoiceId``

- ``/invoice?fields=Total;InvoiceId&BillingPostalCode=!null&BillingCountry=%%ermany``

- ``/invoice?fields=Total;InvoiceDate;InvoiceId;CustomerId&page=2&limit=10``

- ``/invoice?InvoiceDate=(2009-01-01;2009-02-01 00:00:00)``


Example FETCH:

.. code:: bash

    curl --request FETCH \
        --url http://127.0.0.1:5000/customer \
        --header 'content-type: application/json' \
        --data '{
            "fields": [
                "Address",
                "City"
            ],
            "related": {
                "Employee": [
                    "FirstName",
                    "LastName"
                ],
                "Invoice": [
                    "*"
                ]
            },
            "filters": [
                {
                    "model": "Customer",
                    "field": "SupportRepId",
                    "op": "==",
                    "value": 5
                },
                {
                    "model": "Invoice",
                    "field": "Total",
                    "op": ">",
                    "value": 6
                }
            ],
            "sorting": [
                {
                    "model": "Invoice",
                    "field": "Total",
                    "direction": "asc"
                },
                {
                    "model": "Customer",
                    "field": "Address",
                    "direction": "desc"
                }
            ]
        }'

.. _section-3:

Configuration
^^^^^^^^^^^^^

1.  ``AUTOCRUD_METADATA_ENABLED``: *(default: True)* enable metadata endpoint for a resource
2.  ``AUTOCRUD_METADATA_URL``: *(default: '/meta)* added at the end of url resource
3.  ``AUTOCRUD_READ_ONLY``: *(default: False)* enable only http GET method
4.  ``AUTOCRUD_BASE_URL``: *(default: '')* prefix url for resources
5.  ``AUTOCRUD_RESOURCES_URL``: *(default: '/resources')* url for all available resources
6.  ``AUTOCRUD_RESOURCES_URL_ENABLED``: *(default: True)* enable route for resources list
7.  ``AUTOCRUD_SUBDOMAIN``: *(default: None)* bind autocrud endpoints to a subdomain
8.  ``AUTOCRUD_MAX_QUERY_LIMIT``: *(default 1000)* max query limit, 0 means no limit
9.  ``AUTOCRUD_FETCH_ENABLED``: *(default True)* enable or disable FETCH method
10. ``AUTOCRUD_QUERY_STRING_FILTERS_ENABLED``: *(default True)* enable or disable filters in querystring
11. ``AUTOCRUD_EXPORT_ENABLED``: *(default True)* enable or disable export to csv
12. ``AUTOCRUD_DATABASE_SCHEMA``: *(default None)* database schema to consider
13. ``AUTOCRUD_CONDITIONAL_REQUEST_ENABLED``: *(default True)* allow conditional request

License MIT
