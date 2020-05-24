from multiprocessing import cpu_count

from waitress import serve

from .base import BaseApplication


class WSGIWaitress(BaseApplication):
    def run(self):
        """

        :return:
        """
        self.options.setdefault('threads', cpu_count())

        serve(
            self.application,
            host=self._interface,
            port=self._port,
            threads=self.options['threads'],
        )
