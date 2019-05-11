import datetime

from decimal import Decimal

from sqlalchemy.inspection import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.relationships import RelationshipProperty

from .config import ALLOWED_METHODS
from .config import MODEL_VERSION


class Model(object):
    __pks__ = None
    __cols__ = None
    __url__ = None
    __table__ = None
    __hidden__ = []
    __description__ = None
    __version__ = MODEL_VERSION
    __methods__ = ALLOWED_METHODS

    def __str__(self):
        """

        :return:
        """
        return str(getattr(self, self.primary_key_field()))

    @classmethod
    def _load_cols(cls):
        """

        """
        cls.__pks__ = []
        cls.__cols__ = {}

        for i in cls.__dict__:
            if not i.startswith('_') and i not in cls.__hidden__:
                col = getattr(cls, i)
                if isinstance(col, InstrumentedAttribute):
                    if not isinstance(col.comparator, RelationshipProperty.Comparator):
                        cls.__cols__[i] = col
                        if col.primary_key:
                            cls.__pks__.append(i)

    @classmethod
    def columns(cls):
        """

        :return:
        """
        if cls.__cols__ is None:
            cls._load_cols()
        return cls.__cols__

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
    def primary_key_field(cls):
        """

        :return:
        """
        if cls.__pks__ is None:
            cls._load_cols()
        return cls.__pks__[0]

    @classmethod
    def related(cls, name):
        """

        :param name:
        :return:
        """
        columns = None
        instance = None

        if name is not None:
            for r in inspect(cls).relationships:
                if "_".join(r.key.split('_')[:-1]) == name.lower():
                    columns = r.argument.class_().columns()
                    instance = getattr(cls, r.key)

        return instance, columns

    @classmethod
    def description(cls):
        """

        :return:
        """
        return {
            'url': cls.__url__,
            'methods': list(cls.__methods__),
            'description': cls.__description__ or cls.__table__.comment,
            'fields': [
                {
                    'name': col,
                    'type': c.type.python_type.__name__,
                    'primaryKey': c.primary_key,
                    'autoincrement': c.autoincrement,
                    'nullable': c.nullable,
                    'unique': c.unique,
                    'description': c.comment
                } for col, c in cls.columns().items()
            ]
        }

    def to_dict(self, rel=False):
        """

        :param rel:
        :return:
        """
        result = {}
        for col in self.columns().keys():
            value = result[col] = getattr(self, col)

            if isinstance(value, Decimal):
                result[col] = float(value)
            elif isinstance(value, datetime.datetime):
                result[col] = value.isoformat()

        if rel is True:
            for r in inspect(self.__class__).relationships:
                _rel = getattr(self, r.key)
                if isinstance(_rel, Model) or _rel is None:
                    result.update({
                        r.key: _rel.to_dict() if _rel else r.argument().to_dict()
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
            if not r.uselist:
                instance = getattr(self, r.key)
                if instance:
                    link_dict[str(r.key)] = instance.resource_uri()
        return link_dict

    def resource_uri(self):
        """

        :return:
        """
        pk = getattr(self, self.primary_key_field())
        return "{}/{}".format(self.__url__, pk) if pk else None

    def update(self, attributes):
        """

        :param attributes:
        :return:
        """
        for attr, val in attributes.items():
            setattr(self, attr, val)
        return self
