from collections import namedtuple


class HTTP_STATUS:
    SUCCESS = 200
    CREATED = 201
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206
    BAD_REQUEST = 400
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500


ALLOWED_METHODS = {
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'FETCH',
    'HEAD',
    'OPTIONS'
}

MODEL_VERSION = '1'
COLLECTION_SUFFIX = 'List'


def set_default_config(app):
    """

    :param app:
    """
    app.config.setdefault('AUTOCRUD_METADATA_ENABLED', True)
    app.config.setdefault('AUTOCRUD_METADATA_URL', '/meta')
    app.config.setdefault('AUTOCRUD_READ_ONLY', False)
    app.config.setdefault('AUTOCRUD_BASE_URL', '')
    app.config.setdefault('AUTOCRUD_RESOURCES_URL', '/resources')
    app.config.setdefault('AUTOCRUD_SUBDOMAIN', None)
    app.config.setdefault('AUTOCRUD_RESOURCES_URL_ENABLED', True)
    app.config.setdefault('AUTOCRUD_MAX_QUERY_LIMIT', 1000)
    app.config.setdefault('AUTOCRUD_FETCH_ENABLED', True)
    app.config.setdefault('AUTOCRUD_QUERY_STRING_FILTERS_ENABLED', True)


Parsed = namedtuple(
    'Parsed',
    (
        'fields',
        'filters',
        'orders',
        'invalids',
    )
)

Syntax = namedtuple(
    'Syntax',
    (
        'ESCAPE',
        'ALL',
        'SEP',
        'NOT',
        'LIKE',
        'REVERSE',
        'LT',
        'GT',
        'LTE',
        'GTE',
        'NULL',
        'RNS',
        'RNE',
        'NOT_RNS',
        'NOT_RNE',
        'NOT_NULL',
        'NOT_LIKE',
    )
)

scalarFields = namedtuple(
    'scalarFields',
    (
        'page',
        'limit',
        'export',
        'extended',
        'as_table',
    )
)

vectorFields = namedtuple(
    'vector',
    (
        'sort',
        'fields',
    )
)


class Fields:
    scalar = scalarFields(
        page='_page',
        limit='_limit',
        export='_export',
        extended='_extended',
        as_table='_as_table',
    )

    vector = vectorFields(
        sort='_sort',
        fields='_fields',
    )


default_syntax = Syntax(
    ESCAPE='\\',
    ALL='*',
    SEP=';',
    NOT='!',
    REVERSE='-',
    LIKE='%',
    NOT_LIKE='!%',
    LT='__lt__',
    GT='__gt__',
    LTE='__lte__',
    GTE='__gte__',
    NULL='null',
    NOT_NULL='!null',
    RNS='(',
    RNE=')',
    NOT_RNS='!(',
    NOT_RNE=')',
)

default_arguments = Fields
