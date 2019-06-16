class StandaloneApplication:
    def __init__(self, app, *args, **kwargs):
        """

        :param app:
        :param args:
        :param kwargs:
        """
        self._app = app

    def run(self):
        """

        """
        self._app.run()
