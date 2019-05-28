from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty

from .config import ALLOWED_METHODS


class Model(object):
    __pks__ = None
    __cols__ = None
    __rels__ = None
    __url__ = None
    __table__ = None
    __hidden__ = []
    __description__ = None
    __methods__ = ALLOWED_METHODS
    __version__ = '1'

    collection_suffix = 'List'

    def __str__(self):
        """

        :return: (str) primary key value
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
                if isinstance(col.comparator, ColumnProperty.Comparator):
                    cls.__cols__[i] = col
                    if col.primary_key:
                        cls.__pks__.append(i)

    @classmethod
    def _load_related(cls):
        """

        """
        cls.__rels__ = {}

        for r in inspect(cls).relationships:
            if isinstance(r.argument, Mapper):
                key = r.argument.class_.__name__
                columns = r.argument.class_().columns()
            else:
                key = r.argument.__name__
                columns = r.argument.columns()

            instance = getattr(cls, r.key)
            cls.__rels__.update({key: dict(instance=instance, columns=columns)})

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
    def related(cls, name=None):
        """

        :param name:
        :return:
        """
        if not cls.__rels__:
            cls._load_related()

        if name is None:
            return cls.__rels__

        for k in cls.__rels__.keys():
            if k == name:
                return cls.__rels__.get(k).get('instance'),\
                       cls.__rels__.get(k).get('columns')
        return None, None

    @classmethod
    def submodel_from_url(cls, url):
        """

        :param url:
        :return:
        """
        for r in inspect(cls).relationships:
            if isinstance(r.argument, Mapper):
                if r.argument.class_.__url__ == url:
                    return r.argument.class_

    @classmethod
    def validate(cls, data):
        """

        :param data:
        """
        fields = cls.required() + cls.optional()
        unknown = [k for k in data if k not in fields]
        missing = list(set(cls.required()) - set(data.keys()))

        return missing if len(missing) else None, unknown if len(unknown) else None

    @classmethod
    def description(cls):
        """

        :return:
        """
        return dict(
            url=cls.__url__,
            name=cls.__name__,
            methods=list(cls.__methods__),
            description=cls.__description__ or cls.__table__.comment,
            fields=[
                dict(
                    name=col,
                    type=c.type.python_type.__name__,
                    key=c.primary_key,
                    autoincrement=c.autoincrement,
                    nullable=c.nullable,
                    unique=c.unique,
                    description=c.comment
                ) for col, c in cls.columns().items()
            ]
        )

    def to_dict(self, links=False):
        """

        :param links:
        :return:
        """
        resp = {}
        data = self if isinstance(self, dict) else self.__dict__

        for k, v in data.items():
            if k.startswith('_'):
                continue

            if isinstance(v, Model):
                resp.update({v.__class__.__name__: v.to_dict(links)})
            elif isinstance(v, list):
                if len(v) > 0:
                    name = v[0].__class__.__name__ + self.collection_suffix
                    resp.update({name: [i.to_dict(links) for i in v]})
            else:
                resp.update({k: v})

        if links:
            resp['_links'] = self.links()
        return resp

    def links(self):
        """

        :return:
        """
        link_dict = dict(self=self.resource_uri())

        for r in inspect(self.__class__).relationships:
            if not r.uselist:
                instance = getattr(self, r.key)
                if instance:
                    key = r.argument.__name__
                    link_dict[key] = instance.resource_uri()
            elif isinstance(r.argument, Mapper):
                key = r.argument.class_.__name__
                link_dict[key] = "{}{}".format(self.resource_uri(), r.argument.class_.__url__)

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
            if attr in self.columns().keys():
                setattr(self, attr, val)
        return self
