from gevent.pywsgi import WSGIServer


from .base import BaseApplication


class WSGIGevent(BaseApplication, WSGIServer):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        BaseApplication.__init__(self, app, options)
        WSGIServer.__init__(self, (self._interface, self._port), self.application)

    def run(self):
        """

        """
        self.serve_forever()
