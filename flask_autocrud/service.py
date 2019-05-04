from flask import request
from flask import current_app as cap
from flask.views import MethodView

from sqlalchemy import inspect
from sqlalchemy.exc import ArgumentError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager

from sqlalchemy_filters import apply_sort
from sqlalchemy_filters import apply_loads
from sqlalchemy_filters import apply_filters
from sqlalchemy_filters import apply_pagination

from sqlalchemy_filters.exceptions import BadSpec
from sqlalchemy_filters.exceptions import BadSortFormat
from sqlalchemy_filters.exceptions import FieldNotFound
from sqlalchemy_filters.exceptions import BadFilterFormat

from .wrapper import resp_csv
from .wrapper import resp_json
from .wrapper import no_content
from .wrapper import response_with_links
from .wrapper import response_with_location
from .wrapper import response_with_pagination

from .validators import validate_entity
from .validators import parsing_query_string

from .utils import get_pagination_params
from .utils import from_model_to_dict
from .utils import to_flatten_dict

from .config import ARGUMENT
from .config import GRAMMAR
from .config import HTTP_STATUS
from .config import COLLECTION_SUFFIX


class Service(MethodView):
    _db = None
    _model = None

    def delete(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        session = self._db.session()

        resource = model.query.get(resource_id)
        if not resource:
            return resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND)

        session.delete(resource)
        session.commit()
        return no_content()

    def get(self, resource_id=None):
        """

        :param resource_id:
        :return:
        """
        invalid = []
        response = []
        model = self._model
        export = True if ARGUMENT.STATIC.export in request.args else False
        extended = True if ARGUMENT.STATIC.extended in request.args else False

        if resource_id is not None:
            resource = model.query.get(resource_id)
            if not resource:
                return resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND)
            return response_with_links(resource)

        if request.path.endswith(cap.config.get('AUTOCRUD_METADATA_URL')):
            return resp_json(model.description())

        page, limit, error = get_pagination_params(cap.config, request.args)
        invalid += error

        fields, statement, error = parsing_query_string(model)
        invalid += error

        if len(invalid) > 0:
            return resp_json(invalid, 'invalid', code=HTTP_STATUS.BAD_REQUEST)

        statement, pagination = apply_pagination(statement, page, limit)
        resources = statement.all()

        for r in resources:
            item = r.to_dict(True if extended else False)
            item_keys = item.keys()

            if fields:
                for k in set(item_keys) - set(fields):
                    item.pop(k)

            if export and extended:
                item = to_flatten_dict(item)

            response.append(item)

        if export:
            file_name = self._model.__name__
            file_name += ("_" + str(page)) if page else ""
            file_name += ("_" + str(limit)) if limit else ""
            return resp_csv(response, file_name)

        return response_with_pagination(response, pagination)

    def patch(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        session = self._db.session()

        data = request.get_json() or {}
        _, unknown = validate_entity(model, data)
        if unknown:
            return resp_json({'unknown': unknown}, code=HTTP_STATUS.UNPROCESSABLE_ENTITY)

        resource = model.query.get(resource_id)
        if not resource:
            return resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND)

        resource.update(data)
        session.merge(resource)
        session.commit()

        return response_with_links(resource)

    def post(self):
        """

        :return:
        """
        model = self._model
        session = self._db.session()

        data = request.get_json()
        if not data:
            return resp_json({'message': 'Bad Request'}, code=HTTP_STATUS.BAD_REQUEST)

        validate_entity(model, data)
        missing, unknown = validate_entity(model, data)
        if unknown or missing:
            return resp_json({
                'unknown': unknown or [],
                'missing': missing or []
            }, code=HTTP_STATUS.UNPROCESSABLE_ENTITY)

        resource = model.query.filter_by(**data).first()
        if not resource:
            resource = model(**data)
            try:
                session.add(resource)
                session.commit()
            except IntegrityError:
                code = HTTP_STATUS.CONFLICT
            else:
                code = HTTP_STATUS.CREATED
        else:
            code = HTTP_STATUS.CONFLICT

        return response_with_location(resource, code)

    def put(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self._model
        session = self._db.session()

        data = request.get_json() or {}
        validate_entity(model, data)
        _, unknown = validate_entity(model, data)
        if unknown:
            return resp_json({'unknown': unknown}, code=HTTP_STATUS.UNPROCESSABLE_ENTITY)

        resource = model.query.get(resource_id)
        if resource:
            resource.update(data)
            session.merge(resource)
            session.commit()

            return response_with_links(resource)

        resource = model(**data)
        session.add(resource)
        session.commit()

        return response_with_links(resource, HTTP_STATUS.CREATED)

    def fetch(self):
        """

        :return:
        """
        response = []
        invalid = []
        model = self._model
        query = self._db.session.query(self._model)

        data = request.get_json() or {}
        joins = data.get('joins') or {}
        filters = data.get('filters') or []
        fields = data.get('fields') or []
        sort = data.get('sortBy') or []
        export = True if ARGUMENT.STATIC.export in request.args else False
        page, limit, error = get_pagination_params(cap.config, data.get('pagination') or {})
        invalid += error

        cap.logger.debug(query)

        for k in fields:
            if k not in (model.required() + model.optional()):
                invalid.append(k)

        if len(invalid) == 0 and len(fields) > 0:
            query = apply_loads(query, fields)
            cap.logger.debug(query)

        for k in joins.keys():
            instance = None
            for r in inspect(model).relationships:
                if r.key == k.lower() or r.key.split('_collection')[0] == k.lower():
                    instance = getattr(model, r.key)

            if instance is not None:
                joint = joins.get(k)
                try:
                    load_column = contains_eager(instance)
                    if len(joint) > 0 and joint[0] != GRAMMAR.ALL:
                        load_column = load_column.load_only(*joint)

                    query = query.join(instance, aliased=False).options(load_column)
                    cap.logger.debug(query)
                except ArgumentError:
                    invalid += joint
            else:
                invalid.append(k)

        for f in filters:
            try:
                query = apply_filters(query, f)
                cap.logger.debug(query)
            except BadSpec:
                invalid.append(f.get('model'))
            except FieldNotFound:
                invalid.append(f.get('field'))
            except BadFilterFormat:
                invalid.append(f.get('op'))

        for s in sort:
            try:
                query = apply_sort(query, s)
                cap.logger.debug(query)
            except BadSpec:
                invalid.append(s.get('model'))
            except FieldNotFound:
                invalid.append(s.get('field'))
            except BadSortFormat:
                invalid.append(s.get('direction'))

        if len(invalid) > 0:
            return resp_json(invalid, 'invalid', code=HTTP_STATUS.BAD_REQUEST)

        query, pagination = apply_pagination(query, page, limit)
        cap.logger.debug(query)

        for r in query.all():
            zipkeys = {}
            data = from_model_to_dict(r.__dict__)

            if export:
                data = to_flatten_dict(data)

                for key in list(data.keys()):
                    if isinstance(data.get(key), list):
                        zipkeys.update({key.rstrip(COLLECTION_SUFFIX) + '_': data.get(key)})
                        del data[key]

                for zk, value in zipkeys.items():
                    for i in value:
                        response.append({**data, **{zk+k: v for k, v in i.items()}})

            if len(zipkeys.keys()) == 0:
                response.append(data)

        if export:
            file_name = self._model.__name__
            file_name += ("_" + str(page)) if page else ""
            file_name += ("_" + str(limit)) if limit else ""
            return resp_csv(response, file_name)

        return response_with_pagination(response, pagination)
