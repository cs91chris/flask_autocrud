from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

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

    def run(self):
        """

        """
        reactor.listenTCP(self._port, self._site, interface=self._interface)
        reactor.run()
