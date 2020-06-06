import colander
import flask
import sqlalchemy_filters as sqlaf
from flask import current_app as cap
from flask.views import MethodView
from flask_response_builder.dictutils import to_flatten
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import MethodNotAllowed, NotImplemented
from werkzeug.http import generate_etag

from .config import HttpStatus as status
from .qs2sqla import Qs2Sqla
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
        if flask.request.method not in methods:
            raise MethodNotAllowed(valid_methods=list(methods))

        hdr = flask.request.headers.get('X-HTTP-Method-Override') or ''
        if flask.request.method == 'HEAD':
            name = 'GET'
        elif flask.request.method == 'POST':
            name = hdr if hdr.upper() == 'FETCH' else 'POST'
        else:
            name = flask.request.method

        controller = getattr(self, name.lower(), None)
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
            res = {}  # prevent warning
            self._db.session().rollback()
            flask.abort(status.CONFLICT)

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
        data = flask.request.get_json() or {}
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

        if resource_id is None and flask.request.path.endswith(cap.config['AUTOCRUD_METADATA_URL']):
            return self._response.build_response(builder, model.description())

        if subresource is not None:
            model = model.submodel_from_url("/" + subresource)
            if not model:
                flask.abort(status.NOT_FOUND)

        qsqla = Qs2Sqla(model, self.syntax, self.arguments)
        if qsqla.arguments.scalar.related in flask.request.args:
            extended = flask.request.args[qsqla.arguments.scalar.related] or ''
            rels = [r for r in extended.split(qsqla.syntax.SEP) if r]
            model_related = rels if len(rels) > 0 else model.related().keys()
            related.update({k: "*" for k in model_related})

        if resource_id is not None:
            query, _ = qsqla.dict2sqla(dict(filters=filter_by_id, related=related), isouter=True)

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
            data, error = qsqla.parse(flask.request.args)
        else:
            data, error = {}, []

        if resource_id is not None:
            if not data.get('filters'):
                data['filters'] = filter_by_id
            else:
                data['filters'] += filter_by_id

        return self._build_response_list(
            model, builder, {**data, 'related': related}, error, isouter=True,
            only_head=(resource_id is None and flask.request.method == 'HEAD')
        )

    def fetch(self, **kwargs):
        """

        :param kwargs: not used here, but avoid error
        :return:
        """
        _, builder = self._response.get_mimetype_accept()
        override_method = flask.request.headers.get('X-HTTP-Method-Override') or ''
        only_head = override_method.upper() == 'HEAD'

        try:
            schema = FetchPayloadSchema()
            data = schema.deserialize(flask.request.get_json() or {})
        except colander.Invalid as exc:
            data = {}  # prevent warning
            flask.abort(status.UNPROCESSABLE_ENTITY, response=exc.asdict())

        return self._build_response_list(self._model, builder, data, only_head=only_head)

    def _build_response_list(self, model, builder, data, error=None, only_head=False, **kwargs):
        """

        :param model: self model or subresource model
        :param builder: response builder
        :param data: response list: status, header, body
        :param error: previous error to add to response
        :param only_head: enable HEAD method response
        :return:
        """
        qsqla = Qs2Sqla(model, self.syntax, self.arguments)
        invalid = error or []

        export_enabled = cap.config['AUTOCRUD_EXPORT_ENABLED']
        links_enabled = not (
            (export_enabled and qsqla.arguments.scalar.export in flask.request.args)
            or qsqla.arguments.scalar.no_links in flask.request.args
        )

        page, limit, error = qsqla.get_pagination(
            flask.request.args,
            cap.config['AUTOCRUD_MAX_QUERY_LIMIT']
        )
        invalid += error

        query, error = qsqla.dict2sqla(data, **kwargs)
        invalid += error

        if len(invalid) > 0:
            flask.abort(status.BAD_REQUEST, response=dict(invalid=invalid))

        query, pagination = sqlaf.apply_pagination(query, page, limit)
        headers, code = self._pagination_headers(pagination)

        if only_head is True or code == status.NO_CONTENT:
            # return no content with headers and status code
            return self._response.no_content(lambda *arg: (None, code, headers))()

        response = []
        result = query.all()

        for r in result:
            if qsqla.arguments.scalar.as_table in flask.request.args:
                response += to_flatten(r, to_dict=model.to_dict)
            else:
                response.append(r.to_dict(links_enabled))

        if export_enabled:
            if qsqla.arguments.scalar.export in flask.request.args:
                filename = flask.request.args.get(qsqla.arguments.scalar.export)
                filename = filename or "{}{}{}".format(
                    model.__name__,
                    "_{}".format(page) if page else "",
                    "_{}".format(limit) if limit else ""
                )
                csv_builder = self._response.csv(filename=filename)
                return csv_builder(data=response)

        response = {model.__name__ + model.collection_suffix: response}
        if links_enabled:
            response.update({'_meta': self._pagination_meta(pagination)})

        etag = self._compute_etag(response)
        self._check_etag(etag)
        return self._response_with_etag(builder, (response, code, headers), etag)

    def _response_with_etag(self, builder, data, etag):
        """

        :param builder: response builder
        :param data: response list: status, header, body
        :param etag: etag string
        :return:
        """
        response = self._response.build_response(builder, data)

        if cap.config['AUTOCRUD_CONDITIONAL_REQUEST_ENABLED'] is True:
            response.set_etag(etag if isinstance(etag, str) else self._compute_etag(etag))

        return response

    def _validate_new_data(self):
        """
        validates new json resource object

        :return:
        """
        model = self._model
        data = flask.request.get_json()

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

        :param resource: resource object
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

        :param resource: resource object
        :param data: payload
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

        :param pagination: pagination object
        :return:
        """
        args = Qs2Sqla(cls._model).arguments.scalar

        page_number = pagination.page_number
        num_pages = pagination.num_pages
        page_size = pagination.page_size

        if num_pages == 0:
            return dict(first=None, last=None, next=None, prev=None)

        def format_link(p):
            return "{}?{}={}&{}={}".format(flask.request.path, args.page, p, args.limit, page_size)

        return dict(
            first=format_link(1) if page_number > 1 else None,
            last=format_link(num_pages) if page_number != num_pages else None,
            next=format_link(page_number + 1) if page_number != num_pages else None,
            prev=format_link(page_number - 1) if page_number != 1 else None
        )

    @classmethod
    def _pagination_headers(cls, pagination):
        """

        :param pagination: pagination object
        :return:
        """
        total_results = pagination.total_results
        page_number = pagination.page_number
        num_pages = pagination.num_pages
        page_size = pagination.page_size

        link_headers = {}
        headers = {
            'Pagination-Count':     total_results,
            'Pagination-Page':      page_number,
            'Pagination-Num-Pages': num_pages,
            'Pagination-Page-Size': page_size,
        }

        if page_number > num_pages > 0:
            code = status.NO_CONTENT
        elif num_pages == 0:
            code = status.SUCCESS
        else:
            link_headers = cls._link_header(None, **cls._pagination_meta(pagination))
            code = status.SUCCESS if page_number == num_pages else status.PARTIAL_CONTENT

        return {**headers, **link_headers}, code

    @staticmethod
    def _link_header(resource=None, **kwargs):
        """

        :param resource: model object
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

        :param resource: model object
        :return:
        """
        location = resource.links()
        return dict(Location=location.get('self'))

    @classmethod
    def _compute_etag(cls, data):
        """

        :param data: payload
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

        :param data: payload
        :return:
        """
        if cap.config['AUTOCRUD_CONDITIONAL_REQUEST_ENABLED'] is True:
            match = flask.request.if_match
            none_match = flask.request.if_none_match
            etag = data if isinstance(data, str) else cls._compute_etag(data)

            if flask.request.method in ('GET', 'FETCH'):
                if none_match and etag in none_match:
                    flask.abort(flask.Response(status=status.NOT_MODIFIED))
            elif flask.request.method in ('PUT', 'PATCH', 'DELETE'):
                if not match:
                    flask.abort(status.PRECONDITION_REQUIRED)
                elif etag not in match:
                    flask.abort(status.PRECONDITION_FAILED, response={'invalid': etag})
