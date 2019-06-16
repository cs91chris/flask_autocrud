# noinspection PyUnresolvedReferences
from waitress import serve


class StandaloneApplication:
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self._app = app
        self._options = options or {}

    def run(self):
        """

        """
        serve(
            self._app,
            listen=self._options.get('bind'),
            threads=self._options.get('workers')
        )
