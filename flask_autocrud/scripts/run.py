import os
import sys

import click
import yaml
from flask import Flask
from flask_errors_handler import ErrorHandler
from flask_logify import FlaskLogging
from flask_response_builder import ResponseBuilder
from flask_sqlalchemy import SQLAlchemy
from yaml.error import YAMLError

from flask_autocrud import AutoCrud
from flask_autocrud.scripts import DEFAULT_WSGI, wsgi_factory

wsgi_types = click.Choice(DEFAULT_WSGI, case_sensitive=False)


def create_app(config=None):
    """

    :param config:
    :return:
    """
    app = Flask(__name__)
    app.config.update(config or {})

    FlaskLogging(app)
    db = SQLAlchemy(app)
    builder = ResponseBuilder(app)
    error = ErrorHandler(app, response=builder.on_accept())
    autocrud = AutoCrud(app, db, builder=builder, error=error)

    for m in autocrud.models.keys():
        app.logger.info('Registered resource: {}'.format(m))

    error.api_register(app)
    return app


@click.command()
@click.option('-v', '--verbose', is_flag=True, flag_value=True, default=False, help='enable debug mode')
@click.option('-d', '--database', default=None, help='database string connection')
@click.option('-c', '--config', default=None, help='app yaml configuration file')
@click.option('-l', '--log-config', default=None, help='alternative log yaml configuration file')
@click.option('-w', '--wsgi-server', default=None, type=wsgi_types, help='name of wsgi server to use')
@click.option('-b', '--bind', default='127.0.0.1:5000', help='address to bind', show_default=True)
def main(database, config, log_config, bind, verbose, wsgi_server):
    """

    :param database: database string connection
    :param config: app and wsgi configuration file
    :param log_config: log configuration file
    :param bind: address to bind
    :param verbose: enable debug mode
    :param wsgi_server: wsgi server chose
    :return: never returns
    """
    if config is not None:
        try:
            with open(config) as f:
                config = yaml.safe_load(f)
        except (OSError, YAMLError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    else:
        if database is None:
            print('-d is required if no config file provided', file=sys.stderr)
            sys.exit(1)

        env = os.environ.get('FLASK_ENV')
        config = dict(
            app={
                'DEBUG': verbose,
                'SQLALCHEMY_DATABASE_URI': database,
                'SQLALCHEMY_TRACK_MODIFICATIONS': False,
                'ENV': env or ('development' if verbose else 'production')
            },
            wsgi={
                'bind': bind,
                'debug': verbose,
            }
        )

    if log_config is not None:
        config['app']['LOG_FILE_CONF'] = log_config

    # verbose flag overrides config file
    if verbose is True:
        config['app']['DEBUG'] = True

    app = create_app(config.get('app'))
    Standalone = wsgi_factory(wsgi_server or 'builtin')
    Standalone(app, options=config.get('wsgi')).run()


if __name__ == '__main__':
    main()
