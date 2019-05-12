from flask import request
from flask import current_app as cap
from flask.views import MethodView

from sqlalchemy.exc import IntegrityError

import sqlalchemy_filters as sqlaf

from flask_response_builder.dictutils import to_flatten

from . import utils as util
from .qs2sqla import Qs2Sqla
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

            return resource.to_dict(), util.location_header(resource), HTTP_STATUS.CREATED
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

        fields = None
        statement = model.query
        page, limit, error = Qs2Sqla.validate_pagination(request.args, cap.config.get('AUTOCRUD_MAX_QUERY_LIMIT'))
        invalid += error

        if cap.config.get('AUTOCRUD_QUERY_STRING_FILTERS_ENABLED') is True:
            parsed = Qs2Sqla.parse(request.args, model)
            fields = parsed.fields
            invalid += parsed.invalids
            statement = model.query.filter(*parsed.filters).order_by(*parsed.orders)

        if len(invalid) > 0:
            return self._response.build_response(
                builder, ({'invalid': invalid}, HTTP_STATUS.BAD_REQUEST)
            )

        statement, pagination = sqlaf.apply_pagination(statement, page, limit)
        resources = statement.all()

        for r in resources:
            item = r.to_dict(True if Qs2Sqla.arguments.scalar.extended in request.args else False)
            item_keys = item.keys()

            if fields:
                for k in set(item_keys) - set(fields):
                    item.pop(k)

            response.append(item)

        if Qs2Sqla.arguments.scalar.export in request.args:
            return self._export(response, page, limit)

        return self._response.build_response(
            builder, (response, *util.pagination_headers(pagination))
        )

    def fetch(self):
        """

        :return:
        """
        invalid = []
        _, builder = self._response.get_mimetype_accept()

        page, limit, error = Qs2Sqla.validate_pagination(request.args, cap.config.get('AUTOCRUD_MAX_QUERY_LIMIT'))
        invalid += error

        query, error = Qs2Sqla.dict2sqla(self._model, request.get_json() or {})
        invalid += error

        if len(invalid) > 0:
            return self._response.build_response(
                builder, ({'invalid': invalid}, HTTP_STATUS.BAD_REQUEST)
            )

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        result = query.all()

        if Qs2Sqla.arguments.scalar.export in request.args:
            return self._export(result, page, limit, to_dict=util.from_model_to_dict)

        response = []
        for r in result:
            if Qs2Sqla.arguments.scalar.as_table in request.args:
                response += to_flatten(r, to_dict=util.from_model_to_dict)
            else:
                response.append(util.from_model_to_dict(r))

        return self._response.build_response(
            builder, (response, *util.pagination_headers(pagination))
        )

    def _export(self, response, page, limit, **kwargs):
        """

        :param response:
        :param page:
        :param limit:
        :return:
        """
        filename = request.args.get(Qs2Sqla.arguments.scalar.export) or "{}{}{}".format(
            self._model.__name__,
            "_{}".format(page) if page else "",
            "_{}".format(limit) if limit else ""
        )
        return self._response.csv(response, filename=filename, **kwargs)
