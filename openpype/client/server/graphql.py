import collections

import six

ALL_SUBFIELDS = object()


def fields_to_dict(fields):
    if not fields:
        return None

    output = {}
    for field in fields:
        hierarchy = field.split(".")
        last = hierarchy.pop(-1)
        value = output
        for part in hierarchy:
            if value is ALL_SUBFIELDS:
                break

            if part not in value:
                value[part] = {}
            value = value[part]

        if value is not ALL_SUBFIELDS:
            value[last] = ALL_SUBFIELDS
    return output


def project_graphql_from_fields(project_name, fields):
    query = GraphQlQuery("ProjectQuery")
    project_name_var = query.add_variable("projectName", str, project_name)
    project_query = query.add_field("project")
    project_query.filter("name", project_name_var)

    nested_fields = fields_to_dict(fields)

    query_queue = collections.deque()
    for key, value in nested_fields.items():
        if key in ("name", ):
            continue
        query_queue.append((key, value, project_query))

    while query_queue:
        item = query_queue.popleft()
        key, value, parent = item
        field = parent.add_field(key)
        if value is ALL_SUBFIELDS:
            continue

        for k, v in value.items():
            query_queue.append((k, v, field))
    return query


def projects_graphql_from_fields(fields):
    query = GraphQlQuery("ProjectsQuery")
    projects_query = query.add_field("projects", has_edges=True)

    nested_fields = fields_to_dict(fields)

    query_queue = collections.deque()
    for key, value in nested_fields.items():
        query_queue.append((key, value, projects_query))

    while query_queue:
        item = query_queue.popleft()
        key, value, parent = item
        field = parent.add_field(key)
        if value is ALL_SUBFIELDS:
            continue

        for k, v in value.items():
            query_queue.append((k, v, field))
    return query


def value_type_to_string(value_type):
    if value_type in six.string_types:
        return "String"
    raise TypeError("Unknown conversion for {}".format(str(value_type)))


class QueryVariable(object):
    def __init__(self, variable_name):
        self._variable_name = variable_name
        self._name = "${}".format(variable_name)

    @property
    def name(self):
        return self._name

    @property
    def variable_name(self):
        return self._variable_name

    def __hash__(self):
        return self._name.__has__()

    def __str__(self):
        return self._name

    def __format__(self, *args, **kwargs):
        return self._name.__format__(*args, **kwargs)


class GraphQlQuery:
    offset = 2

    def __init__(self, name):
        self._name = name
        self._variables = {}
        self._children = []

    @property
    def indent(self):
        return 0

    @property
    def child_indent(self):
        return self.indent

    def add_variable(self, key, value_type, value=None):
        variable = QueryVariable(key)
        self._variables[key] = {
            "type": value_type, "variable": variable, "value": value
        }
        return variable

    def get_variable(self, key):
        return self._variables[key]["variable"]

    def set_variable_value(self, key, value):
        self._variables[key]["value"] = value

    def get_variable_values(self):
        return {
            key: item["value"]
            for key, item in self._variables.items()
        }

    def add_obj_field(self, field):
        if field in self._children:
            return

        self._children.append(field)
        field.set_parent(self)

    def add_field(self, name, has_edges=None):
        item = GraphQlQueryItem(name, self, has_edges)
        self.add_obj_field(item)
        return item

    def calculate_query(self):
        if not self._children:
            raise ValueError("Missing fields to query")

        variables = []
        for key, item in self._variables.items():
            variables.append(
                "{}: {}!".format(
                    item["variable"], value_type_to_string(item["type"])
                )
            )

        variables_str = ""
        if variables:
            variables_str = "({})".format(",".join(variables))
        header = "query {}{}".format(self._name, variables_str)

        output = []
        output.append(header + " {")
        for field in self._children:
            output.append(field.calculate_query())
        output.append("}")

        return "\n".join(output)


class GraphQlQueryItem:
    def __init__(self, name, parent, has_edges=None):
        if has_edges is None:
            has_edges = False

        self._name = name
        self._parent = parent
        self._has_edges = has_edges

        self._filters = {}

        self._children = []

    @property
    def offset(self):
        return self._parent.offset

    @property
    def indent(self):
        return self._parent.child_indent + self.offset

    @property
    def child_indent(self):
        offset = 0
        if self._has_edges:
            offset = self.offset * 2
        return self.indent + offset

    def filter(self, key, value):
        if isinstance(value, QueryVariable):
            value = str(value)
        self._filters[key] = value

    def add_filter(self, key, value):
        self.filter(key, value)

    def set_parent(self, parent):
        if self._parent is parent:
            return
        self._parent = parent
        parent.add_obj_field(self)

    def add_obj_field(self, field):
        if field in self._children:
            return

        self._children.append(field)
        field.set_parent(self)

    def add_field(self, name, has_edges=None):
        item = GraphQlQueryItem(name, self, has_edges)
        self.add_obj_field(item)
        return item

    def _filters_to_string(self):
        if not self._filters:
            return ""

        filters = []
        for key, value in self._filters.items():
            single_filter = None
            if not isinstance(value, six.string_types):
                try:
                    single_filter = "[{}]".format(
                        ", ".join(
                            '"{}"'.format(item)
                            for item in iter(value)
                        )
                    )
                except TypeError:
                    pass

            if single_filter is None:
                single_filter = "{}: {}".format(key, value)

            filters.append(single_filter)

        return "({})".format(", ".join(filters))

    def calculate_query(self):
        offset = self.indent * " "
        header = "{}{}{}".format(offset, self._name, self._filters_to_string())
        if not self._children:
            if self._has_edges:
                raise ValueError(
                    "Edged item don't have specified child fields"
                )
            return header

        output = []
        output.append(header + " {")
        if self._has_edges:
            edges_offset = offset + self.offset * " "
            node_offset = edges_offset + self.offset * " "
            output.append(edges_offset + "edges {")
            output.append(node_offset + "node {")

        for field in self._children:
            output.append(
                field.calculate_query()
            )

        if self._has_edges:
            output.append(node_offset + "}")
            output.append(edges_offset + "}")
        output.append(offset + "}")

        return "\n".join(output)