from flask import abort
from flask import request

from flask.views import MethodView

from .wrapper import get_json
from .wrapper import resp_csv
from .wrapper import resp_json
from .wrapper import no_content
from .wrapper import response_with_links
from .wrapper import response_with_location

from .validators import validate_entity
from .validators import parsing_query_string


from .config import ARGUMENT
from .config import HTTP_STATUS


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
            abort(resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND))

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
        page = request.args.get(ARGUMENT.STATIC.page)
        limit = request.args.get(ARGUMENT.STATIC.limit)
        export = request.args.get(ARGUMENT.STATIC.export)

        if resource_id is not None:
            resource = model.query.get(resource_id)
            if not resource:
                abort(resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND))
            return response_with_links(resource)

        if request.path.endswith('meta'):
            return resp_json(model.description())

        fields, statement = parsing_query_string(model)

        if page is not None:
            resources = statement.paginate(
                page=int(page) if page else None,
                per_page=int(limit) if limit else None
            ).items
        else:
            resources = statement.limit(limit).all()

        for r in resources:
            item = r.to_dict()
            item_keys = item.keys()
            if fields:
                for k in set(item_keys) - set(fields):
                    item.pop(k)
            response.append(item)

        response_builder = resp_csv if export else resp_json
        return response_builder(response, self.__collection_name__)

    def patch(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        data = get_json()
        validate_entity(model, data)

        resource = model.query.get(resource_id)
        if not resource:
            abort(resp_json({'message': 'Not Found'}, code=HTTP_STATUS.NOT_FOUND))

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
        validate_entity(model, data)

        resource = model.query.filter_by(**data).first()
        if not resource:
            resource = model(**data)
            session.add(resource)
            session.commit()
            code = HTTP_STATUS.CREATED
        else:
            code = HTTP_STATUS.CONFLICT

        return response_with_location(resource, code)

    def put(self, resource_id):
        """

        :param resource_id:
        :return:
        """
        model = self.__model__
        session = self.__db__.session()

        data = get_json()
        validate_entity(model, data)

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
