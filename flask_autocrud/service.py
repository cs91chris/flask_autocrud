import colander

from flask import request
from flask import current_app as cap
from flask.views import MethodView

from sqlalchemy import inspect
import sqlalchemy_filters as sqlaf
from sqlalchemy.exc import IntegrityError

from flask_response_builder.dictutils import to_flatten

from .qs2sqla import Qs2Sqla
from .config import HttpStatus as status
from .validators import FetchPayloadSchema


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
                    status.NOT_FOUND
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
                return dict(unknown=unknown), status.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if not resource:
                return dict(message='Not Found'), status.NOT_FOUND

            res = self._merge_resource(session, resource, data)
            return res, self._link_header(resource)
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
                return dict(message='Bad Request'), status.BAD_REQUEST

            missing, unknown = model.validate(data)
            if unknown or missing:
                return dict(
                    unknown=unknown or [],
                    missing=missing or []
                ), status.UNPROCESSABLE_ENTITY

            resource = model.query.filter_by(**data).first()

            try:
                if resource:
                    raise IntegrityError(statement=None, params=None, orig=None)

                resource = model(**data)
                res = self._add_resource(session, resource)
            except IntegrityError:
                session.rollback()
                return dict(message='Conflict'), status.CONFLICT
            return res, self._location_header(resource), status.CREATED
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
                return dict(unknown=unknown), status.UNPROCESSABLE_ENTITY

            resource = model.query.get(resource_id)
            if resource:
                res = self._merge_resource(session, resource, data)
                return res, self._link_header(resource)

            resource = model(**data)
            res = self._add_resource(session, resource)
            return res, self._location_header(resource), status.CREATED
        return _put()

    def get(self, resource_id=None):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        qsqla = Qs2Sqla(model)
        _, builder = self._response.get_mimetype_accept()

        related = {}
        if qsqla.arguments.scalar.extended in request.args:
            for r in inspect(model).relationships:
                if not r.uselist:
                    related[r.argument.__name__] = ["*"]

        if resource_id is not None:
            query, _ = qsqla.dict2sqla(dict(
                filters=[qsqla.get_filter(model.primary_key_field(), str(resource_id))],
                related=related
            ))
            res = query.one_or_none()

            if not res:
                return self._response.build_response(
                    builder, (dict(message='Not Found'), status.NOT_FOUND)
                )

            return self._response.build_response(
                builder, (res.to_dict(links=True), self._link_header(res))
            )

        if request.path.endswith(cap.config.get('AUTOCRUD_METADATA_URL')):
            return self._response.build_response(builder, model.description())

        if cap.config.get('AUTOCRUD_QUERY_STRING_FILTERS_ENABLED') is True:
            data, error = qsqla.parse(request.args)
        else:
            data, error = {}, []

        return self._build_response_list(builder, {**data, 'related': related}, error)

    def fetch(self):
        """

        :return:
        """
        _, builder = self._response.get_mimetype_accept()

        try:
            schema = FetchPayloadSchema()
            data = schema.deserialize(request.get_json() or {})
        except colander.Invalid as exc:
            return self._response.build_response(builder, (
                dict(message=exc.asdict()), status.UNPROCESSABLE_ENTITY
            ))
        return self._build_response_list(builder, data)

    def _build_response_list(self, builder, data, error=None):
        """

        :param builder:
        :param data:
        :param error:
        :return:
        """
        model = self._model
        qsqla = Qs2Sqla(model)
        invalid = error or []

        page, limit, error = qsqla.get_pagination(
            request.args,
            cap.config.get('AUTOCRUD_MAX_QUERY_LIMIT')
        )
        invalid += error

        query, error = qsqla.dict2sqla(data)
        invalid += error

        if len(invalid) > 0:
            return self._response.build_response(
                builder, (dict(invalid=invalid), status.BAD_REQUEST)
            )

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        result = query.all()

        response = []
        links_enabled = cap.config.get('AUTOCRUD_EXPORT_ENABLED') is False \
            or qsqla.arguments.scalar.export not in request.args

        for r in result:
            if qsqla.arguments.scalar.as_table in request.args:
                response += to_flatten(r, to_dict=model.to_dict)
            else:
                response.append(r.to_dict(links=links_enabled))

        if cap.config.get('AUTOCRUD_EXPORT_ENABLED') is True:
            if qsqla.arguments.scalar.export in request.args:
                filename = request.args.get(qsqla.arguments.scalar.export) or "{}{}{}".format(
                    self._model.__name__,
                    "_{}".format(page) if page else "",
                    "_{}".format(limit) if limit else ""
                )
                return self._response.csv(response, filename=filename)

        return self._response.build_response(
            builder, (response, *self._pagination_headers(pagination))
        )

    @staticmethod
    def _add_resource(session, resource):
        """

        :param session:
        :param resource:
        :return:
        """
        session.add(resource)
        session.flush()
        res = resource.to_dict(links=True)
        session.commit()
        return res

    @staticmethod
    def _merge_resource(session, resource, data):
        """

        :param session:
        :param resource:
        :param data:
        :return:
        """
        session.merge(resource)
        resource.update(data)
        session.flush()
        res = resource.to_dict(links=True)
        session.commit()
        return res

    @staticmethod
    def _link_header(resource):
        """

        :param resource:
        :return:
        """
        links = resource.links()
        link_string = '<{}>; rel=self'.format(links.get('self'))

        for k, l in links.items():
            if k != 'self':
                link_string += ', <{}>; rel=related'.format(l)

        return dict(Link=link_string)

    @staticmethod
    def _location_header(resource):
        """

        :param resource:
        :return:
        """
        location = resource.links()
        return dict(Location=location.get('self'))

    @staticmethod
    def _pagination_headers(pagination):
        """

        :param pagination:
        :return:
        """
        code = status.SUCCESS

        total_results = pagination.total_results
        page_number = pagination.page_number
        num_pages = pagination.num_pages
        page_size = pagination.page_size

        if num_pages > 1 and total_results > page_size:
            code = status.PARTIAL_CONTENT

        if page_number == num_pages:
            code = status.SUCCESS

        return {
            'Pagination-Count': total_results,
            'Pagination-Page': page_number,
            'Pagination-Num-Pages': num_pages,
            'Pagination-Limit': page_size
        }, code
