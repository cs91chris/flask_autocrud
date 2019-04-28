Release Notes
^^^^^^^^^^^^^

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
* bug fix on filter, serching and sorting

Version 1.1.0
--------------

Released 2019-04-07

* added option to set a custom model view
* modified argument list of __init__ and init_app of AutoCrud

Version 1.0.0
--------------

Released 2019-04-03

first version: upload on pypi
