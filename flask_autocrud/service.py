from flask import request
from flask import current_app as cap
from flask.views import MethodView

import sqlalchemy_filters as sqlaf
from sqlalchemy.exc import IntegrityError

from flask_response_builder.dictutils import to_flatten

from .qs2sqla import Qs2Sqla
import flask_autocrud.utils as util


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
                    util.status.NOT_FOUND
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
            _, unknown = model.validate(data)

            if unknown:
                return dict(unknown=unknown), util.status.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if not resource:
                return dict(message='Not Found'), util.status.NOT_FOUND

            session.merge(resource)
            resource.update(data)
            session.flush()
            res = resource.to_dict()
            session.commit()
            return res, util.links_header(resource)
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
                return dict(message='Bad Request'), util.status.BAD_REQUEST

            missing, unknown = model.validate(data)
            if unknown or missing:
                return {
                    'unknown': unknown or [],
                    'missing': missing or []
                }, util.status.UNPROCESSABLE_ENTITY

            resource = model.query.filter_by(**data).first()

            try:
                if resource:
                    raise IntegrityError(statement=None, params=None, orig=None)

                resource = model(**data)
                session.add(resource)
                session.flush()
                res = resource.to_dict()
                session.commit()
            except IntegrityError:
                return dict(message='Conflict'), util.status.CONFLICT
            return res, util.location_header(resource), util.status.CREATED
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
            _, unknown = model.validate(data)

            if unknown:
                return dict(unknown=unknown), util.status.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if resource:
                session.merge(resource)
                resource.update(data)
                session.flush()
                res = resource.to_dict()
                session.commit()
                return res, util.links_header(resource)

            resource = model(**data)
            session.add(resource)
            session.flush()
            res = resource.to_dict()
            session.commit()

            return res, util.location_header(resource), util.status.CREATED
        return _put()

    def get(self, resource_id=None):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        _, builder = self._response.get_mimetype_accept()

        if resource_id is not None:
            r = model.query.get(resource_id)
            if not r:
                return self._response.build_response(
                    builder, (dict(message='Not Found'), util.status.NOT_FOUND)
                )
            return self._response.build_response(
                builder, (r.to_dict(), util.links_header(r))
            )

        if request.path.endswith(cap.config.get('AUTOCRUD_METADATA_URL')):
            return self._response.build_response(builder, model.description())

        if cap.config.get('AUTOCRUD_QUERY_STRING_FILTERS_ENABLED') is True:
            data, error = Qs2Sqla.parse(request.args, model)
        else:
            data, error = {}, []

        return self._build_response_list(builder, data, error)

    def fetch(self):
        """

        :return:
        """
        _, builder = self._response.get_mimetype_accept()
        data = request.get_json() or {}
        return self._build_response_list(builder, data)

    def _build_response_list(self, builder, data, error=None):
        """

        :param builder:
        :param data:
        :param error:
        :return:
        """
        model = self._model
        invalid = error or []

        page, limit, error = Qs2Sqla.get_pagination(request.args, cap.config.get('AUTOCRUD_MAX_QUERY_LIMIT'))
        invalid += error

        query, error = Qs2Sqla.dict2sqla(model, data)
        invalid += error

        if len(invalid) > 0:
            return self._response.build_response(
                builder, (dict(invalid=invalid), util.status.BAD_REQUEST)
            )

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        result = query.all()

        response = []
        for r in result:
            if Qs2Sqla.arguments.scalar.as_table in request.args:
                response += to_flatten(r, to_dict=model.to_dict)
            else:
                response.append(r.to_dict())

        if cap.config.get('AUTOCRUD_EXPORT_ENABLED') is True:
            if Qs2Sqla.arguments.scalar.export in request.args:
                filename = request.args.get(Qs2Sqla.arguments.scalar.export) or "{}{}{}".format(
                    self._model.__name__,
                    "_{}".format(page) if page else "",
                    "_{}".format(limit) if limit else ""
                )
                return self._response.csv(response, filename=filename)

        return self._response.build_response(
            builder, (response, *util.pagination_headers(pagination))
        )
