from flask import abort
from flask import request

from sqlalchemy import asc as ASC
from sqlalchemy import desc as DESC

from .wrapper import resp_json

from .config import GRAMMAR
from .config import ARGUMENT
from .config import HTTP_STATUS


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

    if len(unknown) or len(missing):
        abort(
            resp_json({
                'unknown': unknown,
                'missing': missing
            }, code=HTTP_STATUS.UNPROCESSABLE_ENTITY)
        )


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
        if k in ARGUMENT.STATIC.__dict__.keys():
            continue

        if k.startswith('_') or not v or v == '':
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
