from flask import abort
from flask import request

from sqlalchemy import asc as ASC
from sqlalchemy import desc as DESC
from flask.views import MethodView

from .wrapper import get_json
from .wrapper import resp_csv
from .wrapper import resp_json
from .wrapper import no_content
from .wrapper import response_with_links
from .wrapper import response_with_location


class Service(MethodView):
    __db__ = None
    __model__ = None
    __collection_name__ = 'resources'

    def delete(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        resource = model.query.get(resource_id)
        if not resource:
            abort(resp_json({'message': 'Not Found'}, code=404))

        session.delete(resource)
        session.commit()
        return no_content()

    def get(self, resource_id=None):
        """

        :param resource_id:
        :return:
        """
        response = []
        model = self.__model__

        if resource_id:
            resource = model.query.get(resource_id)
            if not resource:
                abort(resp_json({'message': 'Not Found'}, code=404))

            return response_with_links(resource)

        if request.path.endswith('meta'):
            return resp_json(model.description())

        queryset, limit = self._parsing_query_string()
        resources = queryset.paginate(
            page=int(request.args['page']),
            per_page=limit
        ).items if 'page' in request.args else queryset.limit(limit).all()

        for r in resources:
            item = r.to_dict()
            item_keys = item.keys()
            fields = request.args.get('fields')

            if fields:
                field_list = set(fields.split(';'))
                if not field_list.issubset(item_keys):
                    abort(
                        resp_json({
                            'invalid': list(field_list - item_keys)
                        }, code=400)
                    )

                for k in set(item_keys) - field_list:
                    item.pop(k)
            response.append(item)

        response_builder = resp_csv if 'export' in request.args else resp_json
        return response_builder(response, self.__collection_name__)

    def patch(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        data = get_json()
        self._validate_fields(data)

        resource = model.query.get(resource_id)
        if not resource:
            abort(resp_json({'message': 'Not Found'}, code=404))

        resource.update(data)
        session.merge(resource)
        session.commit()

        return response_with_links(resource)

    def post(self):
        """

        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        data = get_json()
        self._validate_fields(data)

        resource = model.query.filter_by(**data).first()
        if not resource:
            resource = model(**data)
            session.add(resource)
            session.commit()
            code = 201
        else:
            code = 409

        return response_with_location(resource, code)

    def put(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        data = get_json()
        self._validate_fields(data)

        resource = model.query.get(resource_id)
        if resource:
            resource.update(data)
            session.merge(resource)
            session.commit()

            return response_with_links(resource)

        resource = model(**data)

        session.add(resource)
        session.commit()

        return response_with_links(resource, 201)

    def _validate_fields(self, data):
        """

        :param data:
        """
        model = self.__model__
        fields = model.required() + model.optional()
        unknown = [k for k in data if k not in fields]
        missing = set(model.required()) - set(data)

        if len(unknown) or len(missing):
            abort(
                resp_json({
                    'unknown': unknown,
                    'missing': list(missing)
                }, code=422)
            )

    def _parsing_query_string(self):
        """

        :return:
        """
        limit = None
        order = []
        filters = []
        invalid = []
        model = self.__model__
        queryset = model.query

        for k, v in request.args.items():
            if k in ('page', 'export', 'fields'):
                continue

            if hasattr(model, k):
                items = v.split(';')
                if len(items) > 1:
                    if items[0].startswith('!'):
                        items[0] = items[0].lstrip('!')
                        in_statement = ~getattr(model, k).in_(items)
                    else:
                        in_statement = getattr(model, k).in_(items)
                    filters.append(in_statement)
                elif v.startswith('%'):
                    filters.append(getattr(model, k).like(str(v.lstrip('%')), escape='/'))
                else:
                    filters.append(
                        getattr(model, k) != (None if v == '!null' else v.lstrip('!')) if v.startswith('!')
                        else getattr(model, k) == (None if v == 'null' else v.lstrip('\\'))
                    )
            elif k == 'sort':
                for items in v.split(';'):
                    direction = DESC if items.startswith('-') else ASC
                    order.append(direction(getattr(model, items.lstrip('-'))))
            elif k == 'limit':
                limit = int(v)
            else:
                invalid.append(k)

        if len(invalid):
            abort(resp_json({'invalid': invalid}, code=400))

        return queryset.filter(*filters).order_by(*order), limit
