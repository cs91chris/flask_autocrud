import colander


class FilterValue(colander.SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null
        t = type(cstruct)

        if t not in (str, int, float, list):
            raise colander.Invalid(node, "Invalid types, only str, int, float, list are supported")

        return cstruct


class RelatedSchema(colander.SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null

        if type(cstruct) is not dict:
            raise colander.Invalid(node, "Invalid types: it must be dict")

        for k, v in cstruct.items():
            if type(v) is not list:
                raise colander.Invalid(node, "Invalid types of '{}': it must be a list".format(k))
            for i in v:
                if type(i) is not str:
                    raise colander.Invalid(
                        node,
                        "Invalid types of '{}[{}]': it must be a str".format(k, v.index(i))
                    )

        return cstruct


class FilterSchema(colander.MappingSchema):
    model = colander.SchemaNode(colander.String())
    field = colander.SchemaNode(colander.String())
    op = colander.SchemaNode(colander.String())
    value = colander.SchemaNode(FilterValue())


class SortingSchema(colander.MappingSchema):
    model = colander.SchemaNode(colander.String())
    field = colander.SchemaNode(colander.String())
    direction = colander.SchemaNode(colander.String())


class Filters(colander.SequenceSchema):
    filter = FilterSchema()


class Sorting(colander.SequenceSchema):
    sort = SortingSchema()


class FieldsSchema(colander.SequenceSchema):
    fields = colander.SchemaNode(colander.String())


class FetchPayloadSchema(colander.MappingSchema):
    filters = Filters(missing=[])
    sorting = Sorting(missing=[])
    fields = FieldsSchema(missing=[])
    related = colander.SchemaNode(RelatedSchema(), missing={})
