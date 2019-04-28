class GRAMMAR:
    SEP = ';'
    NOT = '!'
    REVERSE = '-'
    NULL = 'null'
    LIKE = '%'
    NOT_NULL = NOT + NULL
    NOT_LIKE = NOT + LIKE


class ARGUMENT:
    class STATIC:
        page = 'page'
        limit = 'limit'
        export = 'export'
        extended = 'extended'

    class DYNAMIC:
        sort = 'sort'
        fields = 'fields'


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


MESSAGES = {
    'DB_NOT_NULL': """
        You can not create AutoCrud without an SQLAlchemy instance.
        Please consider to use the init_app method instead
    """,
    'VIEW_NOT_NULL': """
        You can not create AutoCrud with Admin but without ModelView instance.
        admin and view arguments are required together
    """
}


def set_default_config(app):
    """

    :param app:
    """
    app.config.setdefault('AUTOCRUD_METADATA_ENABLED', True)
    app.config.setdefault('AUTOCRUD_READ_ONLY', False)
    app.config.setdefault('AUTOCRUD_BASE_URL', '')
    app.config.setdefault('AUTOCRUD_RESOURCES_URL', '/resources')
    app.config.setdefault('AUTOCRUD_SUBDOMAIN', None)
    app.config.setdefault('AUTOCRUD_RESOURCES_URL_ENABLED', True)
    app.config.setdefault('AUTOCRUD_QUERY_LIMIT_ENABLED', True)
    app.config.setdefault('AUTOCRUD_MAX_QUERY_LIMIT', 1000)
    app.config.setdefault('AUTOCRUD_FETCH_ENABLED', True)
