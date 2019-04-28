from flask import Blueprint

from flask_json import as_json

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

from flask_autocrud.model import Model
from flask_autocrud.service import Service

from .config import MESSAGES
from .config import set_default_config


class AutoCrud(object):
    def __init__(self, app=None, db=None, admin=None, view=None,
                 exclude_tables=None, user_models=None, schema=None):
        """

        :param db:
        :param app:
        :param admin:
        :param exclude_tables:
        :param user_models:
        :param schema:
        """
        self._app = app
        self._db = db
        self._admin = admin
        self._view = view
        self._api = None
        self._automap_model = None
        self._exclude_tables = exclude_tables
        self._user_models = user_models
        self._schema = schema
        self._models = {}

        if app is not None:
            self.init_app(self._app, self._db, self._admin, self._view)

    def init_app(self, app, db, admin=None, view=None,
                 exclude_tables=None, user_models=None, schema=None):
        """

        :param app:
        :param db:
        :param admin:
        :param view:
        :param exclude_tables:
        :param user_models:
        :param schema:
        :return:
        """
        self._app = app
        self._db = db
        self._admin = admin
        self._view = view
        self._exclude_tables = exclude_tables
        self._user_models = user_models
        self._schema = schema

        if self._db is None:
            raise AttributeError(MESSAGES.get('DB_NOT_NULL'))

        if self._admin and not self._view:
            raise AttributeError(MESSAGES.get('VIEW_NOT_NULL'))

        self._automap_model = automap_base(declarative_base(cls=(db.Model, Model)))
        set_default_config(self._app)

        self._api = Blueprint(
            'flask_autocrud',
            __name__,
            subdomain=self._app.config['AUTOCRUD_SUBDOMAIN']
        )

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
                        cls.__methods__ = {'GET', 'FETCH'}

                    if not self._app.config['AUTOCRUD_FETCH_ENABLED']:
                        cls.__methods__ -= {'FETCH'}

                    self._register_model(cls)

        if self._app.config['AUTOCRUD_RESOURCES_URL_ENABLED']:
            @self._api.route(self._app.config['AUTOCRUD_BASE_URL'] + self._app.config['AUTOCRUD_RESOURCES_URL'])
            @as_json
            def index():
                """

                :return:
                """
                routes = {}
                for name, cls in self._models.items():
                    routes[name] = "{}{{/{}}}".format(cls.__url__, cls.primary_key())
                return routes

        self._app.register_blueprint(self._api)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['autocrud'] = self

    def _register_model(self, cls):
        """

        :param cls:
        """
        if self._admin is not None:
            self._admin.add_view(self._view(cls, self._db.session))

        class_name = cls.__name__
        cls.__url__ = self._app.config['AUTOCRUD_BASE_URL'] + '/' + class_name.lower()

        service_class = type(
            class_name + 'Service',
            (Service,),
            {
                '__model__': cls,
                '__db__': self._db,
                '__collection_name__': class_name
            }
        )

        model_url = cls.__url__
        methods = set(cls.__methods__)
        self._models.update({cls.__name__: cls})
        view_func = service_class.as_view(class_name.lower())

        if 'GET' in methods:
            self._api.add_url_rule(
                model_url,
                defaults={'resource_id': None},
                view_func=view_func,
                strict_slashes=False,
                methods=['GET']
            )

            if self._app.config['AUTOCRUD_METADATA_ENABLED'] is True:
                self._api.add_url_rule(
                    '{resource}{meta}'.format(
                        resource=model_url,
                        meta=self._app.config['AUTOCRUD_METADATA_URL']
                    ),
                    view_func=view_func,
                    methods=['GET']
                )

        if 'POST' in methods:
            self._api.add_url_rule(model_url, view_func=view_func, methods=['POST'])

        if 'FETCH' in methods:
            self._api.add_url_rule(model_url, view_func=view_func, methods=['FETCH'])

        cols = list(cls().__table__.primary_key.columns)

        self._api.add_url_rule(
            '{resource}/<{pk_type}:{pk}>'.format(
                resource=model_url,
                pk='resource_id',
                pk_type=cols[0].type.python_type.__name__ if len(cols) > 0 else 'string'
            ),
            view_func=view_func,
            strict_slashes=False,
            methods=methods - {'POST', 'FETCH'}
        )
