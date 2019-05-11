from collections import namedtuple

from sqlalchemy import asc as sqla_asc
from sqlalchemy import desc as sqla_desc
from sqlalchemy.sql.elements import or_

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

    def parse(self, model):
        """

        :param model:
        :return:
        """
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
                filters = []
                f = model.columns().get(k)
                for item in self._args.getlist(k):
                    if item.startswith(self._grammar.GT):
                        filters.append(f > self.clear_escape(item, escape=self._grammar.GT))
                    elif item.startswith(self._grammar.LT):
                        filters.append(f < self.clear_escape(item, escape=self._grammar.LT))
                    elif item.startswith(self._grammar.GTE):
                        filters.append(f >= self.clear_escape(item, escape=self._grammar.GTE))
                    elif item.startswith(self._grammar.LTE):
                        filters.append(f <= self.clear_escape(item, escape=self._grammar.LTE))
                    elif item.startswith(self._grammar.NOT_LIKE):
                        filters.append(f.notilike(item[2:], escape=self._grammar.ESCAPE))
                    elif item.startswith(self._grammar.LIKE):
                        filters.append(f.ilike(item[1:], escape=self._grammar.ESCAPE))
                    else:
                        item = self.clear_empty(item)
                        if item[0].startswith(self._grammar.NOT):
                            item[0] = self.clear_escape(item[0], escape=self._grammar.NOT)
                            filters.append(f.notin_(item))
                        else:
                            item[0] = self.clear_escape(item[0])
                            filters.append(f.in_(item))
                parsed.filters.append(or_(*filters))
            else:
                parsed.invalids.append(k)

        return parsed
