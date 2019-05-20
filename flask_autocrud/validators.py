from colander import null
from colander import String
from colander import Invalid
from colander import SchemaType
from colander import SchemaNode
from colander import MappingSchema
from colander import SequenceSchema


class FilterValue(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct is null:
            return null
        t = type(cstruct)

        if t not in (str, int, float, list):
            raise Invalid(node, "Invalid types, only str, int, float, list are supported")

        return cstruct


class RelatedSchema(SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct is null:
            return null

        if type(cstruct) is not dict:
            raise Invalid(node, "Invalid types: it must be dict")

        for k, v in cstruct.items():
            if type(v) is not list:
                raise Invalid(node, "Invalid types of '{}': it must be a list".format(k))
            for i in v:
                if type(i) is not str:
                    raise Invalid(node, "Invalid types of '{}[{}]': it must be a str".format(k, v.index(i)))

        return cstruct


class FilterSchema(MappingSchema):
    model = SchemaNode(String())
    field = SchemaNode(String())
    op = SchemaNode(String())
    value = SchemaNode(FilterValue())


class SortingSchema(MappingSchema):
    model = SchemaNode(String())
    field = SchemaNode(String())
    direction = SchemaNode(String())


class Filters(SequenceSchema):
    filter = FilterSchema()


class Sorting(SequenceSchema):
    sort = SortingSchema()


class FieldsSchema(SequenceSchema):
    fields = SchemaNode(String())


class FetchPayloadSchema(MappingSchema):
    filters = Filters(missing=[])
    sorting = Sorting(missing=[])
    fields = FieldsSchema(missing=[])
    related = SchemaNode(RelatedSchema(), missing={})
