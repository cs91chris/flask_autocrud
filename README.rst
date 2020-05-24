Flask-AutoCRUD
==============

Inspired by: `sandman2 <https://github.com/jeffknupp/sandman2>`__

based on: `sqlalchemy-filters <https://pypi.org/project/sqlalchemy-filters>`__
`Flask-ResponseBuilder <https://pypi.org/project/Flask-ResponseBuilder>`__
`Flask-ErrorsHandler <https://pypi.org/project/Flask-ErrorsHandler>`__

Automatically generate a RESTful APIs for CRUD operation and advanced search on a database.
If a list of ``Model`` is not provided, all tables are affected, otherwise you can customize:

- resource name
- fields name
- resource url
- allowed methods
- hidden fields


Features
~~~~~~~~

- HATEOAS support
- conditional requests via ETag header
- full range of CRUD operations
- filtering, sorting and pagination
- customizable responses via query string
- custom FETCH method for advanced search
- content negotiation based on Accept header
- export to csv available
- meta resource description
- cli tool to run autocrud on a database

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

Add filters as query string parameters, they are applied in AND, OR operator not supported.

You can use entity fields as parameter with the following placeholders in the value:

- null value: ``null``
- in operator: list separated by ``;``
- not operator: ``!`` means: not equal, not null, not in
- comparators: ``__gt__`` (grater), ``__lt__`` (lesser), ``__gte__`` (grater-equal), ``__lte__`` (lesser-equal)
- like operator: ``%`` for example: %%test%, %test% or %%test
  NOTE first % are not used in expression, it only indicated that value must be used with like operator.


Other parameters, note that all starts with ``_``:

- Use ``_fields`` parameter to get only the fields listed as value, separated by ``;``.
- Use ``_limit`` and ``_page`` parameters for pagination.
- Sorting is implemented with ``_sort`` parameter. The value is a list of field separated by `;`
  You can prepend ``-`` to reverse order.
- Use ``_export`` parameter to export data into csv format with file name passed as value or leave empty for default.
  You can also use ``Accept:text/csv`` header, but it has a different behavior because the transformation is applied at the
  end of response.
- Use ``_related`` in order to fetch data of related resources listed as value separated by ``;`` or leave empty if
  you want all. Added in 2.2.0 in previous release use ``_extended`` with no filters.
- Use ``_as_table`` in order to flatten nested dict useful if you want render response as table in combination with
  response in html format or simply if you do not want nested json (no value required).
- With ``_no_links`` links of related data and pages are filtered (no value required).

Example requests:

- ``/invoice?InvoiceId=(35;344)``

- ``/invoice?Total=__lte__10&_sort=Total``

- ``/invoice?_fields=BillingCountry;Total;InvoiceId&InvoiceId=!355;344&_sort=-InvoiceId``

- ``/invoice?_fields=Total;InvoiceId&BillingPostalCode=!null&BillingCountry=%%ermany``

- ``/invoice?_fields=Total;InvoiceDate;InvoiceId;CustomerId&_page=2&_limit=10``

- ``/invoice?InvoiceDate=(2009-01-01;2009-02-01 00:00:00)``

- ``/track?_related=Album;Genre``


Custom method FETCH
^^^^^^^^^^^^^^^^^^^

FETCH request is like a GET collection resources with a body that represents the filters to apply. It differs from
filters in query string because there are used to reduce the response (filters are in AND), here are used to
produce a search response, in fact you can request and filter data of combined related resources (like sql JOIN) and
use OR operator with a simple syntax.

See: `sqlalchemy-filters <https://github.com/juliotrigo/sqlalchemy-filters>`__ documentation for filters explanation
and more examples.

If you are unable to use FETCH, you can use POST method with header: ``X-HTTP-Method-Override: FETCH``. If you
want only headers and not response use header: ``X-HTTP-Method-Override: HEAD``.

The following is an example of body request on ``/customer``:

.. code:: json

    {
        "fields": [
            "Address",
            "City"
        ],
        "related": {
            "Employee": [
                "FirstName",
                "LastName"
            ],
            "Invoice": ["*"]
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
    }

.. _section-3:

AutoCRUD cli
^^^^^^^^^^^^

You can use autocrud as a standalone application configurable via yaml file.
Some options could be given via cli see: ``autocrud --help``.

From release 2.2.0 multiple wsgi server can be used,
instead in previous release only gunicorn or waitress can be used;
in addition cli options are changed.

Configuration file contains 2 principal macro section:

- app: every configuration under it will be passed to Flask config object
- wsgi: every configuration under it will be passed to the chosen wsgi server


For example:

.. code:: yaml

    app:
      SQLALCHEMY_DATABASE_URI: sqlite+pysqlite:///examples/db.sqlite3
      SQLALCHEMY_TRACK_MODIFICATIONS: false
    wsgi:
      bind: localhost:5000
      workers: 1
      threads: 1


.. _section-4:

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


TODO
^^^^

* automatic swagger ui or alternative api docs


Feedback and contributions are welcome.

License MIT
