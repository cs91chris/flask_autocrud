import datetime

from decimal import Decimal

from sqlalchemy.inspection import inspect
from flask_admin.contrib.sqla import ModelView


class CustomAdminView(ModelView):
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'
    column_display_pk = True


class Model(object):
    __version__ = '1'

    __url__ = None
    __table__ = None

    __methods__ = {
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE',
        'HEAD',
        'OPTIONS'
        }

    def __str__(self):
        """

        :return:
        """
        return str(getattr(self, self.primary_key()))

    @classmethod
    def required(cls):
        """

        :return:
        """
        columns = []
        for c in cls.__table__.columns:
            is_autoincrement = 'int' in str(c.type).lower() and c.autoincrement
            if (not c.nullable and not c.primary_key) or (c.primary_key and not is_autoincrement):
                columns.append(c.name)
        return columns

    @classmethod
    def optional(cls):
        """

        :return:
        """
        columns = []
        for c in cls.__table__.columns:
            if c.nullable:
                columns.append(c.name)
        return columns

    @classmethod
    def primary_key(cls):
        """

        :return:
        """
        return list(cls.__table__.primary_key.columns)[0].key

    def to_dict(self):
        """

        :return:
        """
        result_dict = {}
        for c in self.__table__.columns.keys():
            value = result_dict[c] = getattr(self, c, None)
            if isinstance(value, Decimal):
                result_dict[c] = float(result_dict[c])
            elif isinstance(value, datetime.datetime):
                result_dict[c] = value.isoformat()
        return result_dict

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
        return self.__url__ + '/' + str(getattr(self, self.primary_key()))

    def update(self, attributes):
        """

        :param attributes:
        :return:
        """
        for attribute in attributes:
            setattr(self, attribute, attributes[attribute])
        return self

    @classmethod
    def description(cls):
        """

        :return:
        """
        description = {}
        for c in cls.__table__.columns:
            column_description = str(c.type)
            if not c.nullable:
                column_description += ' (required)'
            description[c.name] = column_description
        return description
