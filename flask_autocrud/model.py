import datetime

from decimal import Decimal

from sqlalchemy.inspection import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.relationships import RelationshipProperty

from .config import ALLOWED_METHODS
from .config import MODEL_VERSION


class Model(object):
    _pks = None
    _cols = None
    __url__ = None
    __table__ = None
    __description__ = None
    __version__ = MODEL_VERSION
    __methods__ = ALLOWED_METHODS

    def __str__(self):
        """

        :return:
        """
        return self.primary_key()

    @classmethod
    def _load_cols(cls):
        """

        """
        cls._pks = []
        cls._cols = {}

        # CHECK: seems bad but it works
        if cls.__module__ == 'sqlalchemy.ext.automap':
            cls._cols = cls.__table__.columns
            cls._pks += [i.key for i in list(cls.__table__.primary_key.columns)]
        else:
            for i in cls.__dict__:
                if not i.startswith('_'):
                    col = getattr(cls, i)
                    if isinstance(col, InstrumentedAttribute) and \
                            not isinstance(col.comparator, RelationshipProperty.Comparator):
                        cls._cols[i] = col
                        if col.primary_key:
                            cls._pks.append(i)

    @classmethod
    def columns(cls):
        """

        :return:
        """
        if cls._cols is None:
            cls._load_cols()
        return cls._cols

    @classmethod
    def required(cls):
        """

        :return:
        """
        columns = []
        for col, c in cls.columns().items():
            if not (c.nullable or c.primary_key) or (c.primary_key and not c.autoincrement):
                columns.append(col)
        return columns

    @classmethod
    def searchable(cls):
        """

        :return:
        """
        columns = []
        for col, c in cls.columns().items():
            if c.type.python_type is str:
                columns.append(col)
        return columns

    @classmethod
    def optional(cls):
        """

        :return:
        """
        columns = []
        for col, c in cls.columns().items():
            if c.nullable:
                columns.append(col)
        return columns

    @classmethod
    def primary_key(cls):
        """

        :return:
        """
        if cls._pks is None:
            cls._load_cols()
        return cls._pks[0]

    @classmethod
    def description(cls):
        """

        :return:
        """
        description = {
            'url': cls.__url__,
            'methods': list(cls.__methods__),
            'description': cls.__description__ or cls.__table__.comment,
            'fields': []
        }

        for col, c in cls.columns().items():
            description['fields'].append({
                'name': col,
                'type': c.type.python_type.__name__,
                'primaryKey': c.primary_key,
                'autoincrement': c.autoincrement,
                'nullable': c.nullable,
                'unique': c.unique,
                'description': c.comment
            })
        return description

    def to_dict(self, rel=False):
        """

        :param rel:
        :return:
        """
        result = {}
        for col in self.columns().keys():
            value = result[col] = getattr(self, col)

            if isinstance(value, Decimal):
                result[col] = float(result[col])
            elif isinstance(value, datetime.datetime):
                result[col] = value.isoformat()

        if rel is True:
            for r in inspect(self.__class__).relationships:
                instance = getattr(self, r.key)
                if isinstance(instance, Model):
                    result.update({
                        r.key: instance.to_dict()
                    })

                    for i in r.local_columns:
                        result.pop(i.name)

        return result

    def links(self):
        """

        :return:
        """
        link_dict = {'self': self.resource_uri()}
        for r in inspect(self.__class__).relationships:
            if 'collection' not in r.key:
                instance = getattr(self, r.key)
                if instance:
                    link_dict[str(r.key)] = instance.resource_uri()
        return link_dict

    def resource_uri(self):
        """

        :return:
        """
        return "{}/{}".format(self.__url__, self.primary_key())

    def update(self, attributes):
        """

        :param attributes:
        :return:
        """
        for attr, val in attributes.items():
            setattr(self, attr, val)
        return self
