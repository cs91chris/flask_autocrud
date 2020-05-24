import sys
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

    try:
        if name == 'builtin':
            return WSGIBuiltin
        elif name == 'gunicorn':
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
    except ImportError as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        sys.exit(1)
