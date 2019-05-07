from datetime import datetime
from decimal import Decimal

from flask import request

from sqlalchemy import asc as ASC
from sqlalchemy import desc as DESC

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
    page = args.get(ARGUMENT.STATIC.page)
    limit = args.get(ARGUMENT.STATIC.limit)

    page = valid_number(page)
    limit = valid_number(limit)

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

        if k.startswith('_') and k not in ARGUMENT.DYNAMIC.__dict__.values():
            invalid.append(k)

        elif hasattr(model, k):
            attribute = getattr(model, k)
            try:
                if v.startswith(GRAMMAR.NOT_LIKE):
                    filters.append(attribute.notilike(v[2:], escape='/'))
                elif v.startswith(GRAMMAR.LIKE):
                    filters.append(attribute.ilike(v[1:], escape='/'))
                else:
                    v = v.strip(GRAMMAR.SEP)
                    items = v.split(GRAMMAR.SEP)
                    if len(items) > 1:
                        if items[0].startswith(GRAMMAR.NOT):
                            items[0] = items[0].lstrip(GRAMMAR.NOT)
                            in_statement = ~attribute.in_(items)
                        else:
                            in_statement = attribute.in_(items)
                        filters.append(in_statement)
                    else:
                        if v.startswith(GRAMMAR.NOT):
                            filters.append(
                                attribute != (None if v == GRAMMAR.NOT_NULL else v.lstrip(GRAMMAR.NOT))
                            )
                        else:
                            filters.append(
                                attribute == (None if v == GRAMMAR.NULL else v.lstrip('\\'))
                            )
            except AttributeError:
                invalid.append(k)

        elif k == ARGUMENT.DYNAMIC.sort:
            for item in v.split(GRAMMAR.NOT):
                direction = DESC if item.startswith(GRAMMAR.REVERSE) else ASC
                item = item.lstrip(GRAMMAR.REVERSE)

                if not hasattr(model, item):
                    invalid.append(item)
                else:
                    order.append(direction(getattr(model, item)))

        elif k == ARGUMENT.DYNAMIC.fields:
            v = v.strip(GRAMMAR.SEP)
            fields = v.split(GRAMMAR.SEP)
            for item in fields:
                if not hasattr(model, item):
                    invalid.append(item)
        else:
            invalid.append(k)

    return fields, model.query.filter(*filters).order_by(*order), invalid


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
