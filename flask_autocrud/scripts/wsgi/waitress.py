from .base import BaseApplication
from multiprocessing import cpu_count
try:
    from waitress import serve
except ImportError:
    raise ImportError('waitress not installed') from None


class WSGIWaitress(BaseApplication):
    def run(self):
        """

        :return:
        """
        serve(
            self.application,
            listen=self.options.get('bind') or '127.0.0.1:5000',
            threads=self.options.get('workers') or cpu_count()
        )
