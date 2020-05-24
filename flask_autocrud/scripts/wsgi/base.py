class BaseApplication:
    default_host = '127.0.0.1'
    default_port = 5000

    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self.application = app
        self.options = options or {}

        default_bind = '{}:{}'.format(self.default_host, self.default_port)
        bind = (self.options.get('bind') or default_bind).split(':')

        self._interface = bind[0] or self.default_host
        self._port = int(bind[1]) if len(bind) > 1 else self.default_port

    def run(self):
        """

        :return:
        """
        raise NotImplemented


class WSGIBuiltin(BaseApplication):
    def run(self):
        """

        :return:
        """
        debug = self.application.config.get('DEBUG') or False

        self.application.run(
            host=self._interface,
            port=self._port,
            debug=debug
        )
