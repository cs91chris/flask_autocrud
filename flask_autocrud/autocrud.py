from flask import Blueprint

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from flask_autocrud.model import Model
from flask_autocrud.service import Service

from .config import set_default_config

from flask_response_builder import ResponseBuilder


class AutoCrud(object):
    def __init__(self, app=None, db=None, schema=None, models=None, **kwargs):
        """

        :param db:
        :param app:
        :param schema:
        :param models:
        """
        self._models = {}
        self._app = app
        self._db = db
        self._schema = schema
        self._api = None
        self._subdomain = None
        self._baseurl = None
        self._response_builder = ResponseBuilder()

        if app is not None:
            self.init_app(
                self._app, self._db,
                schema=self._schema,
                models=models,
                **kwargs
            )

    @property
    def response_builder(self):
        """

        :return:
        """
        return self._response_builder

    @property
    def models(self):
        """

        :return:
        """
        return self._models

    def init_app(self, app, db, schema=None, models=None, **kwargs):
        """

        :param app:
        :param db:
        :param schema:
        :param models:
        :return:
        """
        self._app = app
        self._db = db
        self._schema = schema

        if self._db is None:
            raise AttributeError(
                "You can not create AutoCrud without an SQLAlchemy instance. "
                "Please consider to use the init_app method instead"
            )

        set_default_config(self._app)
        self.response_builder.init_app(self._app, **kwargs)

        self._subdomain = self._app.config['AUTOCRUD_SUBDOMAIN']
        self._baseurl = self._app.config['AUTOCRUD_BASE_URL']
        self._api = Blueprint('flask_autocrud', __name__, subdomain=self._subdomain)

        if models:
            for m in models:
                self._register_model(m)
        else:
            automap_model = automap_base(declarative_base(cls=(db.Model, Model)))
            automap_model.prepare(self._db.engine, reflect=True, schema=self._schema)

            for model in automap_model.classes:
                if self._app.config['AUTOCRUD_READ_ONLY']:
                    model.__methods__ = {'GET', 'FETCH'}

                if not self._app.config['AUTOCRUD_FETCH_ENABLED']:
                    model.__methods__ -= {'FETCH'}

                self._register_model(model)

        if self._app.config['AUTOCRUD_RESOURCES_URL_ENABLED']:
            self._register_resources_route()

        self._app.register_blueprint(self._api)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['autocrud'] = self

    def _register_model(self, model):
        """

        :param model:
        """
        class_name = model.__name__
        model.__url__ = "{}/{}".format(self._baseurl, class_name.lower())
        view = type(
            class_name + 'Service',
            (Service,), {
                '_model': model,
                '_db': self._db,
                '_response': self.response_builder
            }
        ).as_view(class_name.lower())

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

        pks = list(model().__table__.primary_key.columns)
        pk_type = pks[0].type.python_type.__name__ if len(pks) > 0 else 'string'
        add_route('/<{}:{}>'.format(pk_type, 'resource_id'), model.__methods__ - {'POST', 'FETCH'})
        self.models[model.__name__] = model

    def _register_resources_route(self):
        """

        :return:
        """
        @self._api.route(self._baseurl + self._app.config['AUTOCRUD_RESOURCES_URL'])
        @self.response_builder.on_accept()
        def index():
            routes = {}
            for name, cls in self.models.items():
                routes[name] = "{}{{/{}}}".format(cls.__url__, cls.primary_key_field())
            return routes
