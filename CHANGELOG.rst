Release Notes
^^^^^^^^^^^^^

Version 2.2.0
-------------

Released 2020-05-24

* new _no_links params
* add method override
* support HEAD method for collection resources and search
* add support to filter related resource on query string
* added app factory
* added Flask-Logify extension
* refactored cli: changed options
* added support to multiple wsgi
* fix error handler response
* removed app from members of class AutoCrud

Version 2.1.2
-------------

Released 2020-05-01

* fix setup issue

Version 2.1.1
-------------

Released 2019-12-14

* fix failed tests
* update module version handler
* update dependencies version

Version 2.1.0
-------------

Released 2019-06-16

* new autocrud cli tool
* api problem response on error with Flask-ErrorsHandler

Version 2.0.1
-------------

Released 2019-05-29

* improved tests
* refactored PUT method in order to create resource with no AI pk
* bug fix when pk type is string
* code refinements and bugs fix

Version 2.0.0
-------------

Released 2019-05-21

* conditional request and optimistic locking support
* add _link in ``Model`` to_dict and _meta in collection response in order to support HATEOAS
* subresources url available
* new validators for fetch payload
* query string filters support range definition (between)
* add ``AUTOCRUD_QUERY_STRING_FILTERS_ENABLED`` and ``AUTOCRUD_EXPORT_ENABLED`` config's keys
* add support to hidden fields of ``Model``
* enhancements on query string filters: add grater, less and or conditions. Bug fix on multiple sort condition
* _export query string argument value is used as filename
* add '_' prefix to "internal" query string argument in order to protect resource field with the same name
* bug fix on export when a record has a null foreign key
* add ``Flask-ResponseBuilder`` in order to negotiate the content-type of response
* missing meta url from configuration
* improved management of missing and unknown fields
* ``Model`` support custom attributes name
* removed exclude_tables and update required fields
* removed ``Flask-Admin`` and ``Flask-JSON`` dependencies
* many bug fix and code refinements

Version 1.2.1
-------------

Released 2019-04-28

* fix json body handling, invalid page and limit handling
* add ``AUTOCRUD_METADATA_URL`` configuration
* add ``export`` to csv to ``FETCH`` method
* add ``Total-Count`` header when response is csv
* add support to wildcard ``*`` in order to load all columns of joined table (FETCH)

Version 1.2.0
-------------

Released 2019-04-28

* removed many relationships from ``to_dict`` output of ``Model`` class
* convert nested data into flatten data when using export param
* configurable max and default limit to query
* add pagination header in response to a GET request
* bug fix on query string parser
* Add FETCH method for advanced search. See `sqlalchemy-filters <https://pypi.org/project/sqlalchemy-filters>`__

Version 1.1.4
-------------

Released 2019-04-17

* Replace ``/`` with ``/resources`` endpoint (configurable)
* Enable or disable resource list route via configuration
* Add argument rel to method ``to_dict(rel=False)`` of Model in order to fetch data of related resource
* bug fix on export

Version 1.1.3
--------------

Released 2019-04-13

* bug fix on limit and page parameters
* force strict slashes to False

Version 1.1.2
--------------

Released 2019-04-13

* fix a bug on LIKE operator
* bug fix on sort argument values
* add fields filters

Version 1.1.1
--------------

Released 2019-04-12

* enhancement on filtering: add null, not and in
* bug fix on filter, searching and sorting

Version 1.1.0
--------------

Released 2019-04-07

* added option to set a custom model view
* modified argument list of __init__ and init_app of AutoCrud

Version 1.0.0
--------------

Released 2019-04-03

first version: upload on pypi
