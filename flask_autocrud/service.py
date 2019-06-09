import flask
import colander

from flask import request
from flask import current_app as cap
from flask.views import MethodView

from werkzeug.http import generate_etag
from werkzeug.exceptions import NotImplemented
from werkzeug.exceptions import MethodNotAllowed

import sqlalchemy_filters as sqlaf
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl

from flask_response_builder.dictutils import to_flatten

from .qs2sqla import Qs2Sqla
from .config import HttpStatus as status
from .validators import FetchPayloadSchema


class Service(MethodView):
    _db = None
    _model = None
    _response = None
    syntax = None
    arguments = None

    def dispatch_request(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        methods = self._model.__methods__
        if request.method not in methods:
            raise MethodNotAllowed(valid_methods=list(methods))

        controller = getattr(self, request.method.lower(), None)
        if controller is None:
            raise NotImplemented()

        return controller(*args, **kwargs)

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
                flask.abort(status.NOT_FOUND)

            self._check_etag(resource)
            session.delete(resource)
            session.commit()
        return _delete()

    def post(self):
        """

        :return:
        """
        model = self._model
        _, builder = self._response.get_mimetype_accept()
        data = self._validate_new_data()

        resource = model.query.filter_by(**data).first()

        try:
            if resource:
                raise IntegrityError(statement=None, params=None, orig=None)

            resource = model(**data)
            res = self._add_resource(resource)
        except IntegrityError:
            self._db.session().rollback()
            flask.abort(status.CONFLICT)
            return  # only to prevent warning

        return self._response_with_etag(
            builder, (res, status.CREATED, self._location_header(resource)), res
        )

    def put(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        _, builder = self._response.get_mimetype_accept()
        data = self._validate_new_data()

        resource = model.query.get(resource_id)
        if resource:
            self._check_etag(resource)
            res = self._merge_resource(resource, data)
            return self._response_with_etag(
                builder, (res, self._link_header(resource)), res
            )

        resource = model(**{model.primary_key_field(): resource_id, **data})
        res = self._add_resource(resource)
        return self._response_with_etag(
            builder, (res, self._location_header(resource), status.CREATED), res
        )

    def patch(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        _, builder = self._response.get_mimetype_accept()
        data = request.get_json() or {}
        _, unknown = model.validate(data)

        if unknown:
            flask.abort(status.UNPROCESSABLE_ENTITY, response=dict(unknown=unknown))

        resource = model.query.get(resource_id)
        if not resource:
            flask.abort(status.NOT_FOUND)

        self._check_etag(resource)
        res = self._merge_resource(resource, data)
        return self._response_with_etag(
            builder, (res, self._link_header(resource)), res
        )

    def get(self, resource_id=None, subresource=None):
        """

        :param resource_id:
        :param subresource:
        :return:
        """
        related = {}
        model = self._model
        _, builder = self._response.get_mimetype_accept()

        filter_by_id = [
            Qs2Sqla(model, self.syntax, self.arguments).get_filter(
                model.primary_key_field(), str(resource_id)
            )
        ]

        if request.path.endswith(cap.config['AUTOCRUD_METADATA_URL']):
            return self._response.build_response(builder, model.description())

        if subresource is not None:
            model = model.submodel_from_url("/" + subresource)
            if not model:
                flask.abort(status.NOT_FOUND)

        qsqla = Qs2Sqla(model, self.syntax, self.arguments)
        if qsqla.arguments.scalar.extended in request.args:
            for k, v in model.related().items():
                if isinstance(v['instance'].impl, ScalarObjectAttributeImpl):
                    related.update({k: "*"})

        if resource_id is not None:
            query, _ = qsqla.dict2sqla(dict(filters=filter_by_id, related=related))

            if subresource is None:
                resource = query.one_or_none()
                if not resource:
                    flask.abort(status.NOT_FOUND)

                res = resource.to_dict(links=True)
                self._check_etag(res)

                return self._response_with_etag(
                    builder, (res, self._link_header(resource)), res
                )

        if cap.config['AUTOCRUD_QUERY_STRING_FILTERS_ENABLED'] is True:
            data, error = qsqla.parse(request.args)
        else:
            data, error = {}, []

        if resource_id is not None:
            if data.get('filters') is None:
                data['filters'] = filter_by_id
            else:
                data['filters'] += filter_by_id

        return self._build_response_list(model, builder, {**data, 'related': related}, error)

    def fetch(self):
        """

        :return:
        """
        _, builder = self._response.get_mimetype_accept()

        try:
            schema = FetchPayloadSchema()
            data = schema.deserialize(request.get_json() or {})
        except colander.Invalid as exc:
            flask.abort(status.UNPROCESSABLE_ENTITY, response=exc.asdict())
            return  # only to prevent warning

        return self._build_response_list(self._model, builder, data)

    def _build_response_list(self, model, builder, data, error=None):
        """

        :param model:
        :param builder:
        :param data:
        :param error:
        :return:
        """
        qsqla = Qs2Sqla(model, self.syntax, self.arguments)
        invalid = error or []

        page, limit, error = qsqla.get_pagination(
            request.args,
            cap.config['AUTOCRUD_MAX_QUERY_LIMIT']
        )
        invalid += error

        query, error = qsqla.dict2sqla(data)
        invalid += error

        if len(invalid) > 0:
            flask.abort(status.BAD_REQUEST, response=dict(invalid=invalid))

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        result = query.all()

        response = []
        links_enabled = cap.config['AUTOCRUD_EXPORT_ENABLED'] is False \
            or qsqla.arguments.scalar.export not in request.args

        for r in result:
            if qsqla.arguments.scalar.as_table in request.args:
                response += to_flatten(r, to_dict=model.to_dict)
            else:
                response.append(r.to_dict(links=links_enabled))

        if cap.config['AUTOCRUD_EXPORT_ENABLED'] is True:
            if qsqla.arguments.scalar.export in request.args:
                filename = request.args.get(qsqla.arguments.scalar.export) or "{}{}{}".format(
                    self._model.__name__,
                    "_{}".format(page) if page else "",
                    "_{}".format(limit) if limit else ""
                )
                return self._response.csv(response, filename=filename)

        response = {
            model.__name__ + model.collection_suffix: response,
            '_meta': self._pagination_meta(pagination)
        }

        etag = self._compute_etag(response)
        self._check_etag(etag)

        return self._response_with_etag(
            builder, (response, *self._pagination_headers(pagination)), etag
        )

    def _response_with_etag(self, builder, data, etag):
        """

        :param builder:
        :param data:
        :param etag:
        :return:
        """
        response = self._response.build_response(builder, data)

        if cap.config['AUTOCRUD_CONDITIONAL_REQUEST_ENABLED'] is True:
            response.set_etag(etag if isinstance(etag, str) else self._compute_etag(etag))

        return response

    def _validate_new_data(self):
        """

        :return:
        """
        model = self._model
        data = request.get_json()

        if not data:
            flask.abort(status.BAD_REQUEST)

        missing, unknown = model.validate(data)
        if unknown or missing:
            flask.abort(status.UNPROCESSABLE_ENTITY, response=dict(
                unknown=unknown or [], missing=missing or []
            ))

        return data

    @classmethod
    def _add_resource(cls, resource):
        """

        :param resource:
        :return:
        """
        session = cls._db.session
        session.add(resource)
        session.flush()
        res = resource.to_dict(links=True)
        session.commit()
        return res

    @classmethod
    def _merge_resource(cls, resource, data):
        """

        :param resource:
        :param data:
        :return:
        """
        session = cls._db.session
        session.merge(resource)
        resource.update(data)
        session.flush()
        res = resource.to_dict(links=True)
        session.commit()
        return res

    @classmethod
    def _pagination_meta(cls, pagination):
        """

        :param pagination:
        :return:
        """
        args = Qs2Sqla(cls._model).arguments.scalar

        page_number = pagination.page_number
        num_pages = pagination.num_pages
        page_size = pagination.page_size

        def get_link(p):
            return "{}?{}={}&{}={}".format(request.path, args.page, p, args.limit, page_size)

        return dict(
            first=get_link(1) if page_number > 1 else None,
            last=get_link(num_pages) if page_number != num_pages else None,
            next=get_link(page_number + 1) if page_number != num_pages else None,
            prev=get_link(page_number - 1) if page_number != 1 else None
        )

    @classmethod
    def _pagination_headers(cls, pagination):
        """

        :param pagination:
        :return:
        """
        code = status.SUCCESS

        if not pagination:
            return {}, code

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
            'Pagination-Page-Size': page_size,
            **(cls._link_header(None, **cls._pagination_meta(pagination)) or {})
        }, code

    @staticmethod
    def _link_header(resource=None, **kwargs):
        """

        :param resource:
        :return:
        """
        links = []

        if resource is not None:
            res_links = resource.links()
            links.append('<{}>; rel=self'.format(res_links.get('self')))

            for k, l in res_links.items():
                if k != 'self':
                    links.append('<{}>; rel=related'.format(l))

        for k, l in kwargs.items():
            if l is not None:
                links.append('<{}>; rel={}'.format(l, k))

        return dict(Link=", ".join(links)) if len(links) else {}

    @staticmethod
    def _location_header(resource):
        """

        :param resource:
        :return:
        """
        location = resource.links()
        return dict(Location=location.get('self'))

    @classmethod
    def _compute_etag(cls, data):
        """

        :param data:
        :return:
        """
        if cap.config['AUTOCRUD_CONDITIONAL_REQUEST_ENABLED'] is True:
            if not isinstance(data, str):
                data = str(data if isinstance(data, (dict, list)) else data.to_dict(True))
            return generate_etag(data.encode('utf-8'))
        return ""

    @classmethod
    def _check_etag(cls, data):
        """

        :param data:
        :return:
        """
        if cap.config['AUTOCRUD_CONDITIONAL_REQUEST_ENABLED'] is True:
            match = request.if_match
            none_match = request.if_none_match
            etag = data if isinstance(data, str) else cls._compute_etag(data)

            if request.method in ('GET', 'FETCH'):
                if none_match and etag in none_match:
                    flask.abort(flask.Response(status=status.NOT_MODIFIED))
            elif request.method in ('PUT', 'PATCH', 'DELETE'):
                if not match:
                    flask.abort(status.PRECONDITION_REQUIRED)
                elif etag not in match:
                    flask.abort(status.PRECONDITION_FAILED, response={'invalid': etag})
