from .base import BaseApplication, WSGIBuiltin

DEFAULT_WSGI = (
    'builtin',
    'gunicorn',
    'gevent',
    'tornado',
    'twisted',
    'waitress',
)


def wsgi_factory(name):
    """

    :param name:
    :return:
    """
    if name not in DEFAULT_WSGI:
        raise ValueError("unable to find wsgi server: '{}'".format(name))

    if name == 'builtin':
        return WSGIBuiltin
    if name == 'gunicorn':
        from .gunicorn import WSGIGunicorn
        return WSGIGunicorn
    elif name == 'gevent':
        from .gevent import WSGIGevent
        return WSGIGevent
    elif name == 'tornado':
        from .tornado import WSGITornado
        return WSGITornado
    elif name == 'twisted':
        from .twisted import WSGITwisted
        return WSGITwisted
    elif name == 'waitress':
        from .waitress import WSGIWaitress
        return WSGIWaitress
