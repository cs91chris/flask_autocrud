from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import contains_eager

import sqlalchemy_filters as sqlaf
from sqlalchemy_filters import exceptions

from .config import default_syntax
from .config import default_arguments


class Qs2Sqla:
    def __init__(self, model, syntax=None, arguments=None):
        """

        :param model:
        :param syntax:
        :param arguments:
        """
        self._model = model
        self.syntax = syntax or default_syntax
        self.arguments = arguments or default_arguments

    def clear_empty(self, l, sep=None):
        """

        :param l:
        :param sep:
        :return:
        """
        return [i for i in l.split(sep or self.syntax.SEP) if i != ""]

    def clear_escape(self, i, escape=None):
        """

        :param i:
        :param escape:
        :return:
        """
        esc = escape or self.syntax.ESCAPE
        return i[len(esc):] if i.startswith(esc) else i

    def get_pagination(self, conf, max_limit):
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
        page = valid_number(conf.get(self.arguments.scalar.page))
        limit = valid_number(conf.get(self.arguments.scalar.limit))

        if page is False:
            invalid.append(self.arguments.scalar.page)
        if limit is False:
            invalid.append(self.arguments.scalar.limit)
        if max_limit is False:
            invalid.append('invalid max_limit: {}'.format(max_limit))

        if max_limit > 0:
            page = 1 if not page else page
            if not limit or limit > max_limit:
                limit = max_limit

        return page, limit, invalid

    def get_filter(self, f, v):
        """

        :param f:
        :param v:
        :return:
        """
        def to_dict(op, value):
            """

            :param op:
            :param value:
            :return:
            """
            return dict(model=self._model.__name__, field=f, op=op, value=value)

        if v.startswith(self.syntax.GT):
            return to_dict('>', self.clear_escape(v, escape=self.syntax.GT))
        if v.startswith(self.syntax.LT):
            return to_dict('<', self.clear_escape(v, escape=self.syntax.LT))
        if v.startswith(self.syntax.GTE):
            return to_dict('>=', self.clear_escape(v, escape=self.syntax.GTE))
        if v.startswith(self.syntax.LTE):
            return to_dict('<=', self.clear_escape(v, escape=self.syntax.LTE))
        if v.startswith(self.syntax.NOT_LIKE):
            return to_dict('not_like', self.clear_escape(v, escape=self.syntax.NOT_LIKE))
        if v.startswith(self.syntax.LIKE):
            return to_dict('like', self.clear_escape(v, escape=self.syntax.LIKE))

        if v.startswith(self.syntax.RNS) and v.endswith(self.syntax.RNE):
            down, up = v[len(self.syntax.RNS):-len(self.syntax.RNE)].split(self.syntax.SEP, 1)
            return {'and': [to_dict('>=', down), to_dict('<=', up)]}

        if v.startswith(self.syntax.NOT_RNS) and v.endswith(self.syntax.NOT_RNE):
            down, up = v[len(self.syntax.NOT_RNS):-len(self.syntax.NOT_RNE)].split(self.syntax.SEP, 1)
            return {'or': [to_dict('<', down), to_dict('>', up)]}

        item = self.clear_empty(v)
        if item[0].startswith(self.syntax.NOT):
            item[0] = self.clear_escape(item[0], escape=self.syntax.NOT)
            return to_dict('not_in', item)
        else:
            item[0] = self.clear_escape(item[0])
            return to_dict('in', item)

    def parse(self, args):
        """

        :param args:
        :return:
        """
        invalid = []
        resp = dict(fields=[], filters=[], sorting=[])

        for k, v in args.items():
            if k in self.arguments.scalar:
                continue

            if k == self.arguments.vector.sort:
                for item in self.clear_empty(v):
                    d = 'desc' if item.startswith(self.syntax.REVERSE) else 'asc'
                    item = self.clear_escape(item, escape=self.syntax.REVERSE)

                    if item in self._model.columns().keys():
                        resp['sorting'].append(dict(field=item, direction=d))
                    else:
                        invalid.append(item)

            elif k == self.arguments.vector.fields:
                for item in self.clear_empty(v):
                    if item in self._model.columns().keys():
                        resp['fields'].append(item)
                    else:
                        invalid.append(item)

            elif k in self._model.columns().keys():
                resp['filters'].append({
                    'or': [self.get_filter(k, item) for item in args.getlist(k)]
                })
            else:
                invalid.append(k)
        return resp, invalid

    def dict2sqla(self, data):
        """

        :param data:
        :return:
        """
        invalid = []
        query = self._model.query
        fields = data.get('fields') or list(self._model.columns().keys())
        related = data.get('related') or {}
        filters = data.get('filters') or []
        sort = data.get('sorting') or []

        for k in fields:
            if k not in self._model.columns().keys():
                invalid.append(k)

        if len(invalid) == 0 and len(fields) > 0:
            try:
                query = sqlaf.apply_loads(query, fields)
            except exceptions.BadLoadFormat:
                invalid.append(fields)

        for k in related.keys():
            instance, columns = self._model.related(k)
            if instance is not None:
                _columns = related.get(k)
                try:
                    if len(_columns) > 0 and _columns[0] != self.syntax.ALL:
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
                    _, cols = self._model.related(resource)
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
