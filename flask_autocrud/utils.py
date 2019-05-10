from datetime import datetime
from decimal import Decimal

from flask import request

from sqlalchemy import asc as sqla_asc
from sqlalchemy import desc as sqla_desc
from sqlalchemy.sql.elements import or_

from .model import Model

from .config import GRAMMAR
from .config import ARGUMENT
from .config import HTTP_STATUS
from .config import COLLECTION_SUFFIX


def get_pagination_params(conf, args):
    """

    :param conf:
    :param args:
    :return:
    """
    invalid = []
    page = valid_number(args.get(ARGUMENT.STATIC.page))
    limit = valid_number(args.get(ARGUMENT.STATIC.limit))

    invalid.append(ARGUMENT.STATIC.page) if page is False else None
    invalid.append(ARGUMENT.STATIC.limit) if limit is False else None

    if conf.get('AUTOCRUD_QUERY_LIMIT_ENABLED'):
        page = 1 if not page else page
        max_limit = conf.get('AUTOCRUD_MAX_QUERY_LIMIT')

        if not limit or limit > max_limit:
            limit = conf.get('AUTOCRUD_MAX_QUERY_LIMIT')

    return page, limit, invalid


def from_model_to_dict(data):
    """

    :param data:
    :return:
    """
    resp = {}

    if not isinstance(data, dict):
        data = data.__dict__

    for k, v in data.items():
        if k.startswith('_'):
            continue

        if isinstance(v, Model):
            resp.update({
                v.__class__.__name__: from_model_to_dict(v)
            })
        elif isinstance(v, list):
            if len(v) > 0:
                name = v[0].__class__.__name__ + COLLECTION_SUFFIX
                resp.update({
                    name: [from_model_to_dict(i) for i in v]
                })
        else:
            if isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, datetime):
                v = v.isoformat()

            resp.update({k: v})
    return resp


def valid_number(num):
    """

    :param num:
    :return:
    """
    if num is None:
        return None

    try:
        num = int(num)
        return num if num > 0 else False
    except ValueError:
        return False


def validate_entity(model, data):
    """

    :param model:
    :param data:
    """
    fields = model.required() + model.optional()
    unknown = [k for k in data if k not in fields]
    missing = list(set(model.required()) - set(data.keys()))

    return missing if len(missing) else None, unknown if len(unknown) else None


def parsing_query_string(model):
    """

    :param model:
    :return:
    """
    order = []
    fields = []
    filters = []
    invalid = []

    for k, v in request.args.items():
        if k in ARGUMENT.STATIC.__dict__.values():
            continue

        if k == ARGUMENT.DYNAMIC.sort:
            for item in [i for i in v.split(GRAMMAR.SEP) if i != ""]:
                if item.startswith(GRAMMAR.HIDDEN) or not hasattr(model, item):
                    invalid.append(item)
                else:
                    direction = sqla_desc if item.startswith(GRAMMAR.REVERSE) else sqla_asc
                    item = item.lstrip(GRAMMAR.REVERSE)
                    order.append(direction(getattr(model, item)))
        elif k == ARGUMENT.DYNAMIC.fields:
            for item in [i for i in v.split(GRAMMAR.SEP) if i != ""]:
                if item.startswith(GRAMMAR.HIDDEN) or not hasattr(model, item):
                    invalid.append(item)
                else:
                    fields.append(item)
        elif not k.startswith(GRAMMAR.HIDDEN) and hasattr(model, k):
            or_filters = []
            f = getattr(model, k)
            values = request.args.getlist(k)
            for _v in values:
                if _v.startswith(GRAMMAR.GT):
                    or_filters.append(f > _v.split(GRAMMAR.GT, 1)[1])
                elif _v.startswith(GRAMMAR.LT):
                    or_filters.append(f < _v.split(GRAMMAR.LT, 1)[1])
                elif _v.startswith(GRAMMAR.GTE):
                    or_filters.append(f >= _v.split(GRAMMAR.GTE, 1)[1])
                elif _v.startswith(GRAMMAR.LTE):
                    or_filters.append(f <= _v.split(GRAMMAR.LTE, 1)[1])
                elif _v.startswith(GRAMMAR.NOT_LIKE):
                    or_filters.append(f.notilike(_v[2:], escape=GRAMMAR.ESCAPE))
                elif _v.startswith(GRAMMAR.LIKE):
                    or_filters.append(f.ilike(_v[1:], escape=GRAMMAR.ESCAPE))
                else:
                    items = [i for i in _v.split(GRAMMAR.SEP) if i != ""]
                    if len(items) > 1:
                        if items[0].startswith(GRAMMAR.NOT):
                            items[0] = items[0][1:]
                            or_filters.append(f.notin_(items))
                        else:
                            if items[0].startswith(GRAMMAR.ESCAPE):
                                items[0] = items[0][1:]
                            or_filters.append(f.in_(items))
                    else:
                        if _v.startswith(GRAMMAR.NOT):
                            or_filters.append(f is not None if _v == GRAMMAR.NOT_NULL else f != _v[1:])
                        else:
                            if _v.startswith(GRAMMAR.ESCAPE):
                                _v = _v[1:]
                            or_filters.append(f is None if _v == GRAMMAR.NULL else f == _v)
            filters.append(or_(*or_filters))
        else:
            invalid.append(k)

    query = model.query.filter(*filters).order_by(*order)
    print(query)
    return fields, query, invalid


def links_header(resource):
    """

    :param resource:
    :return:
    """
    links = resource.links()
    link_string = '<{}>; rel=self'.format(links['self'])

    for k, l in links.items():
        if k != 'self':
            link_string += ', <{}>; rel=related'.format(l)

    return {'Link': link_string}


def location_header(resource):
    """

    :param resource:
    :return:
    """
    location = resource.links()
    return {'Location': location['self']}


def pagination_headers(pagination):
    """

    :param pagination:
    :return:
    """
    code = HTTP_STATUS.SUCCESS

    total_results = pagination.total_results
    page_number = pagination.page_number
    num_pages = pagination.num_pages
    page_size = pagination.page_size

    if num_pages > 1 and total_results > page_size:
        code = HTTP_STATUS.PARTIAL_CONTENT

    if page_number == num_pages:
        code = HTTP_STATUS.SUCCESS

    return {
        'Pagination-Count': total_results,
        'Pagination-Page': page_number,
        'Pagination-Num-Pages': num_pages,
        'Pagination-Limit': page_size
    }, code
