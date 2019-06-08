from flask import Blueprint

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from flask_autocrud.model import Model
from flask_autocrud.service import Service
from flask_errors_handler import ErrorHandler
from flask_response_builder import ResponseBuilder

from .config import set_default_config


class AutoCrud(object):
    def __init__(self, app=None, db=None, models=None, builder=None, error=None, **kwargs):
        """

        :param db:
        :param app:
        :param models:
        :param builder:
        :param error:
        """
        self._models = {}
        self._app = app
        self._db = db
        self._api = None
        self._response_error = None
        self._response_builder = None

        if app is not None:
            self.init_app(
                self._app, self._db,
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
    def response_error(self):
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
        self._app = app
        self._response_builder = builder or ResponseBuilder()
        self._response_error = error or ErrorHandler()

        if not isinstance(self._response_builder, ResponseBuilder):
            raise AttributeError(
                "'builder' type must be instance of {}".format(ResponseBuilder.__name__)
            )

        if self._db is None:
            raise AttributeError(
                "You can not create {} without an SQLAlchemy instance. "
                "Please consider to use the init_app method instead".format(
                    self.__class__.__name__
                )
            )

        set_default_config(self._app)
        self._response_builder.init_app(self._app)
        self._response_error.init_app(self._app, response=self._response_builder.on_accept())

        subdomain = self._app.config['AUTOCRUD_SUBDOMAIN']
        self._api = Blueprint('flask_autocrud', __name__, subdomain=subdomain)

        if models is not None:
            for m in models:
                if not issubclass(m, (db.Model, Model)):
                    raise AttributeError(
                        "'{}' must be both a subclass of {} and of {}".format(
                            m, db.Model.__name__, Model.__name__
                        )
                    )
                self._register_model(m, **kwargs)
        else:
            schema = self._app.config['AUTOCRUD_DATABASE_SCHEMA']
            automap_model = automap_base(declarative_base(cls=(db.Model, Model)))
            automap_model.prepare(self._db.engine, reflect=True, schema=schema)

            for model in automap_model.classes:
                if self._app.config['AUTOCRUD_READ_ONLY']:
                    model.__methods__ = {'GET', 'FETCH'}

                if not self._app.config['AUTOCRUD_FETCH_ENABLED']:
                    model.__methods__ -= {'FETCH'}

                self._register_model(model, **kwargs)

        if self._app.config['AUTOCRUD_RESOURCES_URL_ENABLED']:
            self._register_resources_route()

        self._response_error.api_register(self._api)
        self._app.register_blueprint(self._api)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['autocrud'] = self

    def _register_model(self, model, **kwargs):
        """

        :param model:
        """
        class_name = model.__name__
        if model.__url__ is None:
            model.__url__ = "{}/{}".format(
                self._app.config['AUTOCRUD_BASE_URL'],
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

        def add_route(url='', methods=None, **kwargs):
            self._api.add_url_rule(
                model.__url__ + url,
                view_func=view,
                methods=methods or ['GET'],
                strict_slashes=False,
                **kwargs
            )

        if 'GET' in model.__methods__:
            add_route(defaults={'resource_id': None})

            if self._app.config['AUTOCRUD_METADATA_ENABLED'] is True:
                add_route(self._app.config['AUTOCRUD_METADATA_URL'])

        if 'POST' in model.__methods__:
            add_route(methods=['POST'])

        if 'FETCH' in model.__methods__:
            add_route(methods=['FETCH'])

        self._models[model.__name__] = model
        pk = model.columns().get(model.primary_key_field())
        pk_type = pk.type.python_type.__name__
        add_route('/<{}:{}>'.format(pk_type, 'resource_id'), model.__methods__ - {'POST', 'FETCH'})
        add_route('/<{}:{}>/<path:subresource>'.format(pk_type, 'resource_id'), {'GET'})

    def _register_resources_route(self):
        """

        :return:
        """
        url = self._app.config['AUTOCRUD_BASE_URL'] + self._app.config['AUTOCRUD_RESOURCES_URL']

        @self._api.route(url)
        @self.response_builder.on_accept()
        def index():
            return {
                res: "{}{{/{}}}".format(cls.__url__, cls.primary_key_field())
                for res, cls in self._models.items()
            }
