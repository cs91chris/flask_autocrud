from collections import namedtuple

from sqlalchemy import asc as sqla_asc
from sqlalchemy import desc as sqla_desc
from sqlalchemy.sql.elements import or_
from sqlalchemy.sql.elements import between

from .config import Fields
from .config import Grammar


class Qs2Sqla:
    Parsed = namedtuple('Parsed', 'fields filters orders invalids')

    def __init__(self, args, grammar=None, fields=None):
        """

        :param args:
        :param grammar:
        :param fields:
        """
        self._args = args
        self._fields = fields or Fields
        self._grammar = grammar or Grammar

    def clear_empty(self, l):
        """

        :param l:
        :return:
        """
        return [i for i in l.split(self._grammar.SEP) if i != ""]

    def clear_escape(self, i, escape=None):
        """

        :param i:
        :param escape:
        :return:
        """
        esc = escape or self._grammar.ESCAPE
        return i[len(esc):] if i.startswith(esc) else i

    def get_filter(self, f, v):
        """

        :param f:
        :param v:
        :return:
        """
        if v.startswith(self._grammar.GT):
            return f > self.clear_escape(v, escape=self._grammar.GT)
        if v.startswith(self._grammar.LT):
            return f < self.clear_escape(v, escape=self._grammar.LT)
        if v.startswith(self._grammar.GTE):
            return f >= self.clear_escape(v, escape=self._grammar.GTE)
        if v.startswith(self._grammar.LTE):
            return f <= self.clear_escape(v, escape=self._grammar.LTE)

        if v.startswith(self._grammar.NOT_LIKE):
            return f.notilike(
                self.clear_escape(v, escape=self._grammar.NOT_LIKE),
                escape=self._grammar.ESCAPE
            )
        if v.startswith(self._grammar.LIKE):
            return f.ilike(
                self.clear_escape(v, escape=self._grammar.LIKE),
                escape=self._grammar.ESCAPE
            )

        if v.startswith(self._grammar.RNS) and v.endswith(self._grammar.RNE):
            return between(
                f, *v[len(self._grammar.RNS):-len(self._grammar.RNE)].split(self._grammar.SEP, 1)
            )
        if v.startswith(self._grammar.NOT_RNS) and v.endswith(self._grammar.NOT_RNE):
            return ~between(
                f, *v[len(self._grammar.NOT_RNS):-len(self._grammar.NOT_RNE)].split(self._grammar.SEP, 1)
            )

        item = self.clear_empty(v)
        if item[0].startswith(self._grammar.NOT):
            item[0] = self.clear_escape(item[0], escape=self._grammar.NOT)
            return f.notin_(item)
        else:
            item[0] = self.clear_escape(item[0])
            return f.in_(item)

    def parse(self, model):
        """

        :param model:
        :return:
        """
        # noinspection PyCallByClass
        parsed = Qs2Sqla.Parsed(fields=[], filters=[], orders=[], invalids=[])

        for k, v in self._args.items():
            if k in self._fields.Static.__dict__.values():
                continue

            if k == self._fields.Dynamic.sort:
                for item in self.clear_empty(v):
                    if item not in model.columns().keys():
                        parsed.invalids.append(item)
                    else:
                        direction = sqla_desc if item.startswith(self._grammar.REVERSE) else sqla_asc
                        item = self.clear_escape(item, escape=self._grammar.REVERSE)
                        parsed.orders.append(direction(model.columns().get(item)))

            elif k == self._fields.Dynamic.fields:
                for item in self.clear_empty(v):
                    if item not in model.columns().keys():
                        parsed.invalids.append(item)
                    else:
                        parsed.fields.append(item)

            elif k in model.columns().keys():
                f = model.columns().get(k)
                parsed.filters.append(
                    or_(*[self.get_filter(f, item) for item in self._args.getlist(k)])
                )
            else:
                parsed.invalids.append(k)
        return parsed
