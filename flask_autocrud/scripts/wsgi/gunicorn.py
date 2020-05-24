from gunicorn.app.base import BaseApplication as WSGIServer
from six import iteritems

from .base import BaseApplication


class WSGIGunicorn(BaseApplication, WSGIServer):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        BaseApplication.__init__(self, app, options)
        WSGIServer.__init__(self)

    def load_config(self):
        """

        """
        options = {}

        for k, v in iteritems(self.options):
            if k in self.cfg.settings and v is not None:
                options.update({k: v})

        for key, value in iteritems(options):
            self.cfg.set(key.lower(), value)

    def load(self):
        """

        :return:
        """
        return self.application

    def init(self, parser, opts, args):
        """

        :param parser:
        :param opts:
        :param args:
        """
        # abstract in superclass

    def run(self):
        """

        """
        WSGIServer.run(self)
