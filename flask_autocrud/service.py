from flask import request
from flask import current_app as cap
from flask.views import MethodView

from sqlalchemy import inspect
from sqlalchemy.exc import ArgumentError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager

import sqlalchemy_filters as sqlaf
from sqlalchemy_filters import exceptions

from flask_response_builder.dictutils import to_flatten

from . import utils as util
from .config import ARGUMENT
from .config import GRAMMAR
from .config import HTTP_STATUS


class Service(MethodView):
    _db = None
    _model = None
    _response = None

    def delete(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        @self._response.no_content
        def _delete():
            mime_type, _ = self._response.get_mimetype_accept()

            model = self._model
            session = self._db.session()
            resource = model.query.get(resource_id)

            if not resource:
                return (
                    {'message': 'Not Found'},
                    {'Content-Type': mime_type},
                    HTTP_STATUS.NOT_FOUND
                )

            session.delete(resource)
            session.commit()

        return _delete()

    def patch(self, resource_id):
        """

        :param resource_id:
        :return:
        """

        @self._response.on_accept()
        def _patch():
            model = self._model
            session = self._db.session()
            data = request.get_json() or {}
            _, unknown = util.validate_entity(model, data)

            if unknown:
                return {'unknown': unknown}, HTTP_STATUS.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if not resource:
                return {'message': 'Not Found'}, HTTP_STATUS.NOT_FOUND

            resource.update(data)
            session.merge(resource)
            session.commit()
            return resource.to_dict(), util.links_header(resource)
        return _patch()

    def post(self):
        """

        :return:
        """
        @self._response.on_accept()
        def _post():
            model = self._model
            session = self._db.session()
            data = request.get_json()

            if not data:
                return {'message': 'Not Found'}, HTTP_STATUS.BAD_REQUEST

            missing, unknown = util.validate_entity(model, data)
            if unknown or missing:
                return {
                    'unknown': unknown or [],
                    'missing': missing or []
                }, HTTP_STATUS.UNPROCESSABLE_ENTITY

            resource = model.query.filter_by(**data).first()

            try:
                if resource:
                    raise IntegrityError(statement=None, params=None, orig=None)

                resource = model(**data)
                session.add(resource)
                session.commit()
            except IntegrityError:
                return {'message': 'Conflict'}, HTTP_STATUS.CONFLICT

            return data, util.location_header(resource), HTTP_STATUS.CREATED
        return _post()

    def put(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        @self._response.on_accept()
        def _put():
            model = self._model
            session = self._db.session()
            data = request.get_json() or {}
            _, unknown = util.validate_entity(model, data)

            if unknown:
                return {'unknown': unknown}, HTTP_STATUS.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if resource:
                resource.update(data)
                session.merge(resource)
                session.commit()
                return resource.to_dict(), util.links_header(resource)

            resource = model(**data)
            session.add(resource)
            session.commit()

            return data, util.location_header(resource), HTTP_STATUS.CREATED
        return _put()

    def get(self, resource_id=None):
        """

        :param resource_id:
        :return:
        """
        invalid = []
        response = []
        model = self._model
        _, builder = self._response.get_mimetype_accept()

        if resource_id is not None:
            resource = model.query.get(resource_id)
            if not resource:
                return self._response.build_response(
                    builder, ({'message': 'Not Found'}, HTTP_STATUS.NOT_FOUND)
                )
            return self._response.build_response(
                builder, (resource.to_dict(), util.links_header(resource))
            )

        if request.path.endswith(cap.config.get('AUTOCRUD_METADATA_URL')):
            return self._response.build_response(builder, model.description())

        page, limit, error = util.get_pagination_params(cap.config, request.args)
        invalid += error

        fields, statement, error = util.parsing_query_string(model)
        invalid += error

        if len(invalid) > 0:
            return self._response.build_response(
                builder, ({'invalid': invalid}, HTTP_STATUS.BAD_REQUEST)
            )

        statement, pagination = sqlaf.apply_pagination(statement, page, limit)
        resources = statement.all()

        for r in resources:
            item = r.to_dict(True if ARGUMENT.STATIC.extended in request.args else False)
            item_keys = item.keys()

            if fields:
                for k in set(item_keys) - set(fields):
                    item.pop(k)

            response.append(item)

        if ARGUMENT.STATIC.export in request.args:
            return self._export(response, page, limit)

        return self._response.build_response(
            builder, (response, *util.pagination_headers(pagination))
        )

    def fetch(self):
        """

        :return:
        """
        _, builder = self._response.get_mimetype_accept()

        invalid = []
        model = self._model
        query = self._db.session.query(self._model)

        data = request.get_json() or {}
        fields = data.get('fields') or []
        joins = data.get('related') or {}
        filters = data.get('filters') or []
        sort = data.get('sorting') or []
        pagination = data.get('pagination') or {}

        page, limit, error = util.get_pagination_params(cap.config, pagination)
        invalid += error

        cap.logger.debug(query)

        for k in fields:
            if k not in (model.required() + model.optional()):
                invalid.append(k)

        if len(invalid) == 0 and len(fields) > 0:
            try:
                query = sqlaf.apply_loads(query, fields)
                cap.logger.debug(query)
            except exceptions.BadLoadFormat:
                invalid.append(fields)

        for k in joins.keys():
            instance = None
            for r in inspect(model).relationships:
                if "_".join(r.key.split('_')[:-1]) == k.lower():
                    instance = getattr(model, r.key)

            if instance is not None:
                column = joins.get(k)
                try:
                    load_column = contains_eager(instance)
                    if len(column) > 0 and column[0] != GRAMMAR.ALL:
                        load_column = load_column.load_only(*column)

                    query = query.join(instance, aliased=False).options(load_column)
                    cap.logger.debug(query)
                except ArgumentError:
                    invalid += column
            else:
                invalid.append(k)

        for f in filters:
            try:
                query = sqlaf.apply_filters(query, f)
                cap.logger.debug(query)
            except exceptions.BadSpec:
                invalid.append(f.get('model'))
            except exceptions.FieldNotFound:
                invalid.append(f.get('field'))
            except exceptions.BadFilterFormat:
                invalid.append(f.get('op'))

        for s in sort:
            try:
                query = sqlaf.apply_sort(query, s)
                cap.logger.debug(query)
            except exceptions.BadSpec:
                invalid.append(s.get('model'))
            except exceptions.FieldNotFound:
                invalid.append(s.get('field'))
            except exceptions.BadSortFormat:
                invalid.append(s.get('direction'))

        if len(invalid) > 0:
            return self._response.build_response(
                builder, ({'invalid': invalid}, HTTP_STATUS.BAD_REQUEST)
            )

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        cap.logger.debug(query)

        response = []
        result = query.all()

        if ARGUMENT.STATIC.export in request.args:
            return self._export(response, page, limit)

        for r in result:
            if ARGUMENT.STATIC.as_table in request.args:
                response += to_flatten(r, to_dict=util.from_model_to_dict)
            else:
                response.append(util.from_model_to_dict(r))

        return self._response.build_response(
            builder, (response, *util.pagination_headers(pagination))
        )

    def _export(self, response, page, limit):
        """

        :param response:
        :param page:
        :param limit:
        :return:
        """
        filename = request.args.get(ARGUMENT.STATIC.export) or "{}{}{}".format(
            self._model.__name__,
            "_{}".format(page) if page else "",
            "_{}".format(limit) if limit else ""
        )
        return self._response.csv(response, filename=filename)
