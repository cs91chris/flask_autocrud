class GRAMMAR:
    SEP = ';'
    NOT = '!'
    REVERSE = '-'
    NULL = 'null'
    LIKE = '%'
    NOT_NULL = NOT + NULL


class ARGUMENT:
    class STATIC:
        page = 'page'
        limit = 'limit'
        export = 'export'

    class DYNAMIC:
        sort = 'sort'
        fields = 'fields'


class HTTP_STATUS:
    SUCCESS = 200
    CREATED = 201
    NO_CONTENT = 204
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
    'HEAD',
    'OPTIONS'
}

MODEL_VERSION = '1'
