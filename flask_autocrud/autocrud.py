from flask import Blueprint

from flask_json import as_json

from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from flask_autocrud.model import Model
from flask_autocrud.service import Service
from flask_autocrud.model import CustomAdminView


class AutoCrud(object):
    def __init__(self, app=None, db=None, admin=None,
                 exclude_tables=None, user_models=None, schema=None):
        """

        :param db:
        :param app:
        :param admin:
        :param exclude_tables:
        :param user_models:
        :param schema:
        """
        self._db = db
        self._admin = admin
        self._api = None
        self._automap_model = None
        self._exclude_tables = exclude_tables
        self._user_models = user_models
        self._schema = schema

        if app is not None:
            if db is None:
                raise AttributeError(
                    "You can not create AutoCrud without an SQLAlchemy instance. "
                    "Please consider to use the init_app method instead"
                )
            self._app = app
            self.init_app(self._app, self._db)
        else:
            self._app = None

    def init_app(self, app, db, admin=None,
                 exclude_tables=None, user_models=None, schema=None):
        """

        :param app:
        :param db:
        :param admin:
        :param exclude_tables:
        :param user_models:
        :param schema:
        :return:
        """
        self._app = app
        self._db = db
        self._admin = admin

        self._exclude_tables = exclude_tables
        self._user_models = user_models
        self._schema = schema

        self._app.classes = []
        self._automap_model = automap_base(declarative_base(cls=(db.Model, Model)))
        self._config()

        with self._app.app_context():
            if self._user_models:
                if any([issubclass(cls, self._automap_model) for cls in self._user_models]):
                    self._automap_model.prepare(self._db.engine, reflect=True, schema=self._schema)

                for user_model in self._user_models:
                    self._register_model(user_model)
            else:
                self._automap_model.prepare(self._db.engine, reflect=True, schema=self._schema)

                for cls in self._automap_model.classes:
                    if self._exclude_tables and cls.__table__.name in self._exclude_tables:
                        continue

                    if self._app.config['AUTOCRUD_READ_ONLY']:
                        cls.__methods__ = {'GET'}

                    self._register_model(cls)

        @self._app.route(self._app.config['AUTOCRUD_BASE_URL'])
        @as_json
        def index():
            """

            :return:
            """
            routes = {}
            for cls in self._app.classes:
                routes[cls.__model__.__name__] = '{}{{/{}}}'.format(
                    cls.__model__.__url__,
                    cls.__model__.primary_key()
                )
            return routes

        self._app.register_blueprint(self._api)

    def _register_model(self, cls):
        """

        :param cls:
        """
        if self._admin is not None:
            self._admin.add_view(CustomAdminView(cls, self._db.session))

        cls.__url__ = '{}{}'.format(
            self._app.config['AUTOCRUD_BASE_URL'],
            cls.__name__.lower()
        )
        cols = list(cls().__table__.primary_key.columns)

        service_class = type(
            cls.__name__ + 'Service',
            (Service,),
            {
                '__model__': cls,
                '__db__': self._db,
                '__collection_name__': cls.__name__
            }
        )

        primary_key_type = 'string'
        if len(cols) == 1:
            col_type = cols[0].type
            if isinstance(col_type, sqltypes.String):
                primary_key_type = 'string'
            elif isinstance(col_type, sqltypes.Integer):
                primary_key_type = 'int'
            elif isinstance(col_type, sqltypes.Numeric):
                primary_key_type = 'float'

        cls = service_class
        endpoint = self._api
        self._app.classes.append(cls)

        view_func = cls.as_view(service_class.__name__.lower())
        methods = set(cls.__model__.__methods__)

        if 'GET' in methods:
            endpoint.add_url_rule(
                cls.__model__.__url__ + '/',
                defaults={'resource_id': None},
                view_func=view_func,
                methods=['GET']
            )
            if self._app.config['AUTOCRUD_METADATA_ENABLED'] is True:
                endpoint.add_url_rule(
                    '{resource}/meta'.format(resource=cls.__model__.__url__),
                    view_func=view_func,
                    methods=['GET']
                )

        if 'POST' in methods:
            endpoint.add_url_rule(
                cls.__model__.__url__ + '/',
                view_func=view_func,
                methods=['POST'],
                strict_slashes=False
            )

        endpoint.add_url_rule(
            '{resource}/<{pk_type}:{pk}>'.format(
                resource=cls.__model__.__url__,
                pk='resource_id',
                pk_type=primary_key_type
            ),
            view_func=view_func,
            methods=methods - {'POST'}
        )

    def _config(self):
        """

        """
        self._app.config.setdefault('AUTOCRUD_METADATA_ENABLED', True)
        self._app.config.setdefault('AUTOCRUD_READ_ONLY', False)
        self._app.config.setdefault('AUTOCRUD_BASE_URL', '/')
        self._app.config.setdefault('AUTOCRUD_SUBDOMAIN', None)

        self._app.config.setdefault('JSON_ADD_STATUS', False)
        self._app.config.setdefault('JSON_DECODE_ERROR_MESSAGE', 'Invalid JSON')

        self._api = Blueprint(
            'flask_autocrud',
            __name__,
            subdomain=self._app.config['AUTOCRUD_SUBDOMAIN']
        )
