try:
    from gevent.pywsgi import WSGIServer
except ImportError:
    raise ImportError('gevent not installed') from None

from .base import BaseApplication


class WSGIGevent(BaseApplication, WSGIServer):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        BaseApplication.__init__(self, app, options)

        try:
            listener = self.options.get('bind').split(':')
        except AttributeError:
            listener = ('0.0.0.0', 5000)

        WSGIServer.__init__(listener, self.app)

    def run(self):
        """

        """
        WSGIGevent.run(self)
