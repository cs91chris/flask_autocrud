from datetime import datetime
from decimal import Decimal

from collections import MutableMapping

from .model import Model
from .config import ARGUMENT
from .validators import valid_number


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

    for k, v in data.items():
        if k.startswith('_'):
            continue

        if isinstance(v, Model):
            resp.update({
                v.__class__.__name__: from_model_to_dict(v.__dict__)
            })
        elif isinstance(v, list):
            if len(v) > 0:
                name = v[0].__class__.__name__ + 'List'
                resp.update({
                    name: [from_model_to_dict(i.__dict__) for i in v]
                })
        else:
            if isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, datetime):
                v = v.isoformat()

            resp.update({k: v})
    return resp


def to_flatten_dict(d, parent_key='', sep='_'):
    """

    :param d:
    :param parent_key:
    :param sep:
    :return:
    """
    items = []

    for k, v in d.items():
        new_key = (parent_key + sep + k) if parent_key else k

        if isinstance(v, MutableMapping):
            items.extend(to_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
