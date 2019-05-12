from sqlalchemy import asc as sqla_asc
from sqlalchemy import desc as sqla_desc
from sqlalchemy.sql.elements import or_

from .config import Parsed
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
    def get_filter(cls, f, v):
        """

        :param f:
        :param v:
        :return:
        """
        if v.startswith(cls.syntax.GT):
            return f > cls.clear_escape(v, escape=cls.syntax.GT)
        if v.startswith(cls.syntax.LT):
            return f < cls.clear_escape(v, escape=cls.syntax.LT)
        if v.startswith(cls.syntax.GTE):
            return f >= cls.clear_escape(v, escape=cls.syntax.GTE)
        if v.startswith(cls.syntax.LTE):
            return f <= cls.clear_escape(v, escape=cls.syntax.LTE)

        if v.startswith(cls.syntax.NOT_LIKE):
            return f.notilike(
                cls.clear_escape(v, escape=cls.syntax.NOT_LIKE),
                escape=cls.syntax.ESCAPE
            )
        if v.startswith(cls.syntax.LIKE):
            return f.ilike(
                cls.clear_escape(v, escape=cls.syntax.LIKE),
                escape=cls.syntax.ESCAPE
            )

        if v.startswith(cls.syntax.RNS) and v.endswith(cls.syntax.RNE):
            return f.between(
                *v[len(cls.syntax.RNS):-len(cls.syntax.RNE)].split(cls.syntax.SEP, 1)
            )
        if v.startswith(cls.syntax.NOT_RNS) and v.endswith(cls.syntax.NOT_RNE):
            return ~f.between(
                *v[len(cls.syntax.NOT_RNS):-len(cls.syntax.NOT_RNE)].split(cls.syntax.SEP, 1)
            )

        item = cls.clear_empty(v)
        if item[0].startswith(cls.syntax.NOT):
            item[0] = cls.clear_escape(item[0], escape=cls.syntax.NOT)
            return f.notin_(item)
        else:
            item[0] = cls.clear_escape(item[0])
            return f.in_(item)

    @classmethod
    def parse(cls, args, model):
        """

        :param args:
        :param model:
        :return:
        """
        # noinspection PyCallByClass
        parsed = Parsed(fields=[], filters=[], orders=[], invalids=[])

        for k, v in args.items():
            if k in cls.arguments.scalar:
                continue

            if k == cls.arguments.vector.sort:
                for item in cls.clear_empty(v):
                    direction = sqla_desc if item.startswith(cls.syntax.REVERSE) else sqla_asc
                    item = cls.clear_escape(item, escape=cls.syntax.REVERSE)

                    if item in model.columns().keys():
                        parsed.orders.append(direction(model.columns().get(item)))
                    else:
                        parsed.invalids.append(item)

            elif k == cls.arguments.vector.fields:
                for item in cls.clear_empty(v):
                    if item in model.columns().keys():
                        parsed.fields.append(item)
                    else:
                        parsed.invalids.append(item)

            elif k in model.columns().keys():
                f = model.columns().get(k)
                parsed.filters.append(
                    or_(*[cls.get_filter(f, item) for item in args.getlist(k)])
                )
            else:
                parsed.invalids.append(k)
        return parsed
