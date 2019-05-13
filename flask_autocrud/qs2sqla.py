from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import contains_eager

import sqlalchemy_filters as sqlaf
from sqlalchemy_filters import exceptions

from .config import default_syntax
from .config import default_arguments


class Qs2Sqla:
    syntax = default_syntax
    arguments = default_arguments

    @classmethod
    def clear_empty(cls, l):
        """

        :param l:
        :return:
        """
        return [i for i in l.split(cls.syntax.SEP) if i != ""]

    @classmethod
    def clear_escape(cls, i, escape=None):
        """

        :param i:
        :param escape:
        :return:
        """
        esc = escape or cls.syntax.ESCAPE
        return i[len(esc):] if i.startswith(esc) else i

    @classmethod
    def get_pagination(cls, conf, max_limit):
        """

        :param conf:
        :param max_limit:
        :return:
        """
        def valid_number(num):
            if num is None:
                return None

            try:
                num = int(num)
                return num if num > 0 else False
            except ValueError:
                return False

        invalid = []
        max_limit = valid_number(max_limit)
        page = valid_number(conf.get(cls.arguments.scalar.page))
        limit = valid_number(conf.get(cls.arguments.scalar.limit))

        if page is False:
            invalid.append(cls.arguments.scalar.page)
        if limit is False:
            invalid.append(cls.arguments.scalar.limit)
        if max_limit is False:
            invalid.append('invalid max_limit: {}'.format(max_limit))

        if max_limit > 0:
            page = 1 if not page else page
            if not limit or limit > max_limit:
                limit = max_limit

        return page, limit, invalid

    @classmethod
    def get_filter(cls, f, v):
        """

        :param f:
        :param v:
        :return:
        """
        if v.startswith(cls.syntax.GT):
            return dict(field=f, op='>', value=cls.clear_escape(v, escape=cls.syntax.GT))
        if v.startswith(cls.syntax.LT):
            return dict(field=f, op='<', value=cls.clear_escape(v, escape=cls.syntax.LT))
        if v.startswith(cls.syntax.GTE):
            return dict(field=f, op='>=', value=cls.clear_escape(v, escape=cls.syntax.GTE))
        if v.startswith(cls.syntax.LTE):
            return dict(field=f, op='<=', value=cls.clear_escape(v, escape=cls.syntax.LTE))
        if v.startswith(cls.syntax.NOT_LIKE):
            return dict(field=f, op='not_like', value=cls.clear_escape(v, escape=cls.syntax.NOT_LIKE))
        if v.startswith(cls.syntax.LIKE):
            return dict(field=f, op='like', value=cls.clear_escape(v, escape=cls.syntax.LIKE))

        if v.startswith(cls.syntax.RNS) and v.endswith(cls.syntax.RNE):
            down, up = v[len(cls.syntax.RNS):-len(cls.syntax.RNE)].split(cls.syntax.SEP, 1)
            return {
                'and': [
                    dict(field=f, op='>=', value=down),
                    dict(field=f, op='<=', value=up)
                ]
            }

        if v.startswith(cls.syntax.NOT_RNS) and v.endswith(cls.syntax.NOT_RNE):
            down, up = v[len(cls.syntax.NOT_RNS):-len(cls.syntax.NOT_RNE)].split(cls.syntax.SEP, 1)
            return {
                'or': [
                    dict(field=f, op='<', value=down),
                    dict(field=f, op='>', value=up)
                ]
            }

        item = cls.clear_empty(v)
        if item[0].startswith(cls.syntax.NOT):
            item[0] = cls.clear_escape(item[0], escape=cls.syntax.NOT)
            return dict(field=f, op='not_in', value=item)
        else:
            item[0] = cls.clear_escape(item[0])
            return dict(field=f, op='in', value=item)

    @classmethod
    def parse(cls, args, model):
        """

        :param args:
        :param model:
        :return:
        """
        invalid = []
        resp = dict(fields=[], filters=[], sorting=[])

        for k, v in args.items():
            if k in cls.arguments.scalar:
                continue

            if k == cls.arguments.vector.sort:
                for item in cls.clear_empty(v):
                    d = 'desc' if item.startswith(cls.syntax.REVERSE) else 'asc'
                    item = cls.clear_escape(item, escape=cls.syntax.REVERSE)

                    if item in model.columns().keys():
                        resp['sorting'].append(dict(field=item, direction=d))
                    else:
                        invalid.append(item)

            elif k == cls.arguments.vector.fields:
                for item in cls.clear_empty(v):
                    if item in model.columns().keys():
                        resp['fields'].append(item)
                    else:
                        invalid.append(item)

            elif k in model.columns().keys():
                resp['filters'].append({
                    'or': [cls.get_filter(k, item) for item in args.getlist(k)]
                })
            else:
                invalid.append(k)
        return resp, invalid

    @classmethod
    def dict2sqla(cls, model, data):
        invalid = []
        query = model.query
        fields = data.get('fields') or list(model.columns().keys())
        related = data.get('related') or {}
        filters = data.get('filters') or []
        sort = data.get('sorting') or []

        for k in fields:
            if k not in model.columns().keys():
                invalid.append(k)

        if len(invalid) == 0 and len(fields) > 0:
            try:
                query = sqlaf.apply_loads(query, fields)
            except exceptions.BadLoadFormat:
                invalid.append(fields)

        for k in related.keys():
            instance, columns = model.related(k)
            if instance is not None:
                _columns = related.get(k)
                try:
                    if len(_columns) > 0 and _columns[0] != cls.syntax.ALL:
                        _invalid = list(set(related.get(k)) - set(columns))
                        if len(_invalid) > 0:
                            _columns = _invalid
                            raise ArgumentError
                    else:
                        _columns = columns

                    query = query.join(instance, aliased=False)
                    query = query.options(contains_eager(instance).load_only(*_columns))
                except ArgumentError:
                    invalid += _columns
            else:
                invalid.append(k)

        def apply(stm, flt, action):
            """

            :param stm:
            :param flt:
            :param action:
            :return:
            """
            resource = flt.get('model')
            try:
                if resource:
                    _, cols = model.related(resource)
                    if cols and cols.get(flt.get('field')) is None:
                        raise exceptions.FieldNotFound

                return action(stm, flt)
            except exceptions.BadSpec:
                invalid.append(resource)
            except exceptions.FieldNotFound:
                invalid.append(flt.get('field'))
            except exceptions.BadFilterFormat:
                invalid.append(flt.get('op'))
            except exceptions.BadSortFormat:
                invalid.append(flt.get('direction'))

        for f in filters:
            try:
                query = apply(query, f, sqlaf.apply_filters)
            except AttributeError:
                invalid.append(f)

        for s in sort:
            try:
                query = apply(query, s, sqlaf.apply_sort)
            except AttributeError:
                invalid.append(s)

        return query, invalid
