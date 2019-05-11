class Grammar:
    ESCAPE = '\\'
    ALL = '*'
    SEP = ';'
    NOT = '!'
    LIKE = '%'
    REVERSE = '-'
    LT = '__lt__'
    GT = '__gt__'
    LTE = '__lte__'
    GTE = '__gte__'
    NULL = 'null'
    RNS = '('
    RNE = ')'
    NOT_RNS = NOT + RNS
    NOT_RNE = RNE
    NOT_NULL = NOT + NULL
    NOT_LIKE = NOT + LIKE


class Fields:
    class Static:
        page = '_page'
        limit = '_limit'
        export = '_export'
        extended = '_extended'
        as_table = '_as_table'

    class Dynamic:
        sort = '_sort'
        fields = '_fields'


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
