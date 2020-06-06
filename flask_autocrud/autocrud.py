import flask
from flask_errors_handler import ErrorHandler
from flask_response_builder import ResponseBuilder
from sqlalchemy.ext.automap import automap_base

from .config import HttpStatus, set_default_config
from .model import Model
from .service import Service


class AutoCrud(object):
    def __init__(self, app=None, db=None, models=None, builder=None, error=None, **kwargs):
        """

        :param db:
        :param app:
        :param models:
        :param builder:
        :param error:
        """
        self._db = db
        self._api = None
        self._models = {}
        self._response_error = None
        self._response_builder = None

        if app is not None:
            self.init_app(
                app, self._db,
                models=models, builder=builder, error=error,
                **kwargs
            )

    @property
    def blueprint(self):
        """

        :return:
        """
        return self._api

    @property
    def response_builder(self):
        """

        :return:
        """
        return self._response_builder

    @property
    def error_handler(self):
        """

        :return:
        """
        return self._response_error

    @property
    def models(self):
        """

        :return:
        """
        return self._models

    def init_app(self, app, db, models=None, builder=None, error=None, **kwargs):
        """

        :param app:
        :param db:
        :param models:
        :param builder:
        :param error:
        :return:
        """
        self._db = db
        self._response_error = error
        self._response_builder = builder

        if not self._response_builder:
            self._response_builder = ResponseBuilder()
            self._response_builder.init_app(app)
        if not self._response_error:
            self._response_error = ErrorHandler()
            self._response_error.init_app(app, response=self._response_builder.on_accept())

        set_default_config(app)

        subdomain = app.config['AUTOCRUD_SUBDOMAIN']
        self._api = flask.Blueprint('flask_autocrud', __name__, subdomain=subdomain)

        if models is not None:
            for m in models:
                if not issubclass(m, (db.Model, Model)):
                    raise ValueError(
                        "'{}' must be both a subclass of {} and of {}".format(m, db.Model, Model)
                    )
                self._register_model(m, app.config, **kwargs)
        else:
            schema = app.config['AUTOCRUD_DATABASE_SCHEMA']
            automap_model = automap_base(cls=(db.Model, Model))
            automap_model.prepare(self._db.engine, reflect=True, schema=schema)

            for model in automap_model.classes:
                self._register_model(model, app.config, **kwargs)
                if app.config['AUTOCRUD_READ_ONLY']:
                    model.__methods__ = {'OPTION', 'HEAD', 'GET', 'FETCH'}

                if not app.config['AUTOCRUD_FETCH_ENABLED']:
                    model.__methods__ -= {'FETCH'}

        if app.config['AUTOCRUD_RESOURCES_URL_ENABLED']:
            self._register_resources_route(
                app.config['AUTOCRUD_BASE_URL'] + app.config['AUTOCRUD_RESOURCES_URL']
            )

        self._response_error.api_register(self._api)
        app.register_blueprint(self._api)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['autocrud'] = self

    def _register_model(self, model, conf, **kwargs):
        """

        :param model:
        :param conf:
        """
        def add_route(url='', methods=None, **params):
            """

            :param url:
            :param methods:
            :param params:
            """
            self._api.add_url_rule(
                model.__url__ + url,
                view_func=view,
                methods=methods,
                strict_slashes=False,
                **params
            )

        class_name = model.__name__
        if model.__url__ is None:
            model.__url__ = "{}/{}".format(
                conf['AUTOCRUD_BASE_URL'],
                class_name.lower()
            )

        view = type(
            class_name + 'Service',
            (Service,), {
                '_model': model,
                '_db': self._db,
                '_response': self._response_builder,
                **kwargs
            }
        ).as_view(class_name)

        add_route(methods=['POST', 'FETCH'])
        add_route(defaults={'resource_id': None})

        if conf['AUTOCRUD_METADATA_ENABLED'] is True:
            add_route(conf['AUTOCRUD_METADATA_URL'])

        self._models[model.__name__] = model
        pk = model.columns().get(model.primary_key_field())
        pk_type = pk.type.python_type.__name__
        add_route('/<{}:{}>'.format(pk_type, 'resource_id'), model.__methods__ - {'POST', 'FETCH'})
        add_route('/<{}:{}>/<path:subresource>'.format(pk_type, 'resource_id'), {'GET'})

    def _register_resources_route(self, url):
        """

        :return:
        """
        @self._api.route(url)
        @self.response_builder.on_accept()
        def index():
            if not self._models:
                flask.abort(HttpStatus.NOT_FOUND, 'no resources available')

            response = {}
            for res, cls in self._models.items():
                response[res] = cls.__url__

            return response
