try:
    from twisted.web.server import Site
    from twisted.internet import reactor
    from twisted.web.wsgi import WSGIResource
except ImportError:
    raise ImportError('twisted not installed') from None

from .base import BaseApplication


class WSGITwisted(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        BaseApplication.__init__(self, app, options)
        resource = WSGIResource(reactor, reactor.getThreadPool(), self.application)
        self._site = Site(resource)

        bind = (self.options.get('bind') or '127.0.0.1:5000').split(':')
        self._interface = bind[0]
        self._port = int(bind[1]) if len(bind) > 1 else 5000

    def run(self):
        """

        """
        reactor.listenTCP(self._port, self._site, interface=self._interface)
        reactor.run()
