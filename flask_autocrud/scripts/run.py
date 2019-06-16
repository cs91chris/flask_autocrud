import yaml
import argparse

from yaml.error import YAMLError

from flask import Flask

from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy
from flask_errors_handler import ErrorHandler

try:
    from .gunicorn import StandaloneApplication
except (ModuleNotFoundError, ImportError):
    try:
        from .waitress import StandaloneApplication
    except (ModuleNotFoundError, ImportError):
        from .default import StandaloneApplication


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--database', default=None)
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-b', '--bind', default='0.0.0.0:5000')
    parser.add_argument('-w', '--workers', default=1)
    parser.add_argument('-c', '--config', default=None)
    args = parser.parse_args()

    if args.config is not None:
        try:
            with open(args.config) as f:
                config = yaml.safe_load(f)
        except (FileNotFoundError, YAMLError) as exc:
            import sys
            print(exc, file=sys.stderr)
            sys.exit(1)
    else:
        config = {
            'app': {
                'DEBUG': args.debug,
                'SQLALCHEMY_DATABASE_URI': args.database,
                'SQLALCHEMY_TRACK_MODIFICATIONS': False
            },
            'wsgi': {
                'bind': args.bind,
                'workers': args.workers,
                'debug': args.debug
            }
        }

    app = Flask(__name__)
    app.config.update(config.get('app', {}))

    error = ErrorHandler(app)
    error.api_register(app)
    AutoCrud(app, SQLAlchemy(app), error=error)

    StandaloneApplication(app, config.get('wsgi', {})).run()


if __name__ == '__main__':
    main()
