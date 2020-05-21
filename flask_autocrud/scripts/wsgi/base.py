class BaseApplication:
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self.application = app
        self.options = options or {}

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
        self.application.run(
            host=self.application.config.get('APP_HOST') or '127.0.0.1',
            port=self.application.config.get('APP_PORT') or 5000,
            debug=self.application.config.get('DEBUG') or False
        )
