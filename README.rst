Flask-AutoCRUD
==============

Based on `sandman2 <https://github.com/jeffknupp/sandman2>`__ and
`sqlalchemy-filters <https://pypi.org/project/sqlalchemy-filters>`__.

Automatically generate a RESTful API service for CRUD operation on database.
If a list of tables or a list of sqlalchemy model is not provided, all tables are affected.


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
    - like operator: ``%`` for example: %%test%, %test% or %%test.
      NOTE first % are not used in expression, it only indicated that value must be used with like operator.

Other parameters:

    - Use ``_fields`` parameter to get only the fields listes as value, separated by ``;``.
    - Use ``_limit`` and ``_page`` parameters for pagination.
    - Sorting is implemented with ``_sort`` parameter. The value is a list of field separated by `;`
      You can prepend ``-`` to reverse order.
    - Use ``_export`` parameter to export data into csv format.
    - Use ``_extended`` in order to fetch data of related resources.

Example requests:

http://127.0.0.1:5000/invoice?fields=BillingCountry;Total;InvoiceId&InvoiceId=!355;344&sort=-InvoiceId

http://127.0.0.1:5000/invoice?fields=Total;InvoiceId&BillingPostalCode=!null&BillingCountry=%%ermany

http://127.0.0.1:5000/invoice?fields=Total;InvoiceDate;InvoiceId;CustomerId&page=2&limit=10

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

License MIT
