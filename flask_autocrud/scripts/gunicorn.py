# noinspection PyUnresolvedReferences
from gunicorn.app.base import BaseApplication
from six import iteritems


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self.application = app
        self.options = options or {}
        super(StandaloneApplication, self).__init__()

    def init(self, parser, opts, args):
        """

        :param parser:
        :param opts:
        :param args:
        """
        pass

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
