########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import networkx as nx

from dsl_parser import exceptions
from dsl_parser.framework import elements
from dsl_parser.framework.requirements import Requirement


class Parser(object):

    def _init_element_context(self, value, element_cls, element_name, inputs):
        context = Context(self, inputs)
        self._traverse_element_cls(element_cls=element_cls,
                                   name=element_name,
                                   value=value,
                                   parent_element=None,
                                   context=context)
        context.calculate_element_graph()
        return context

    def _traverse_element_cls(self,
                              element_cls,
                              name,
                              value,
                              parent_element,
                              context):
        element = element_cls(name=name,
                              initial_value=value,
                              context=context)
        context.add_element(element, parent=parent_element)
        self._traverse_schema(schema=element_cls.schema,
                              parent_element=element,
                              context=context)

    def _traverse_schema(self, schema, parent_element, context):
        if isinstance(schema, dict):
            self._traverse_dict_schema(schema=schema,
                                       parent_element=parent_element,
                                       context=context)
        elif isinstance(schema, elements.ElementType):
            self._traverse_element_type_schema(
                schema=schema,
                parent_element=parent_element,
                context=context)
        elif isinstance(schema, list):
            self._traverse_list_schema(schema=schema,
                                       parent_element=parent_element,
                                       context=context)
        else:
            raise exceptions.DSLParsingFormatException(1)

    def _traverse_dict_schema(self, schema,  parent_element, context):
        for name, element_cls in schema.items():
            # TODO: move to schema structure validation
            if not isinstance(name, basestring):
                raise exceptions.DSLParsingFormatException(
                    1, 'Schema keys must be strings for {0} but'
                       ' found {1}'.format(parent_element.name,
                                           name))
            # TODO: move to schema structure validation
            if not (isinstance(element_cls, type) and
                    issubclass(element_cls, elements.Element) and
                    element_cls != elements.Element):
                raise exceptions.DSLParsingFormatException(
                    1, 'Schema values must be strict subclasses of Element'
                       ' but found {0}'.format(element_cls))

            # TODO: once the above is moved to specific schema structure
            # validate, this condition should be moved to the beginning
            # of this function
            if not isinstance(parent_element.initial_value, dict):
                continue

            if name not in parent_element.initial_value:
                value = None
            else:
                value = parent_element.initial_value[name]
            self._traverse_element_cls(element_cls=element_cls,
                                       name=name,
                                       value=value,
                                       parent_element=parent_element,
                                       context=context)

    def _traverse_element_type_schema(self, schema, parent_element, context):
        element_cls = schema.type
        if isinstance(schema, elements.Leaf):
            # TODO: move to schema structure validation
            if not (isinstance(element_cls, type) or
                    (isinstance(element_cls, (list, tuple)) and
                     len(element_cls) > 0 and
                     all([isinstance(e, type) for e in element_cls]))):
                raise exceptions.DSLParsingFormatException(
                    1, 'ElementType type attribute must be a type or a '
                       'list/tuple of types')
            return

        # TODO: move to schema structure validation
        if not (isinstance(element_cls, type) and
                issubclass(element_cls, elements.Element) and
                element_cls != elements.Element):
            raise exceptions.DSLParsingFormatException(
                1, 'Illegal element type specified: {0}'.format(element_cls))

        if isinstance(schema, elements.Dict):
            if not isinstance(parent_element.initial_value, dict):
                return
            for name, value in parent_element.initial_value.items():
                self._traverse_element_cls(element_cls=element_cls,
                                           name=name,
                                           value=value,
                                           parent_element=parent_element,
                                           context=context)
        elif isinstance(schema, elements.List):
            if not isinstance(parent_element.initial_value, list):
                return
            for index, value in enumerate(parent_element.initial_value):
                self._traverse_element_cls(element_cls=element_cls,
                                           name=index,
                                           value=value,
                                           parent_element=parent_element,
                                           context=context)
        else:
            raise exceptions.DSLParsingFormatException(1)

    def _traverse_list_schema(self, schema, parent_element, context):
        for schema_item in schema:
            self._traverse_schema(schema=schema_item,
                                  parent_element=parent_element,
                                  context=context)

    def _iterate_elements(self, context, strict):
        for element in context.elements_graph_topological_sort():
            required_args = self._extract_element_requirements(
                element=element,
                context=context)
            self._validate_element(element, required_args, strict=strict)
            self._parse_element(element, required_args)

    @staticmethod
    def _validate_element(element, required_args, strict):
        value = element.initial_value
        if element.required and value is None:
            raise exceptions.DSLParsingFormatException(
                1,
                'Missing required value for {0}'.format(element.name))

        def validate_schema(schema):
            if isinstance(schema, (dict, elements.Dict)):
                if not isinstance(value, dict):
                    raise exceptions.DSLParsingFormatException(
                        1, 'Expected dict value for {0} but found {1}'
                           .format(element.name, value))
                for key in value.keys():
                    if not isinstance(key, basestring):
                        raise exceptions.DSLParsingFormatException(
                            1, 'Dict keys must be strings for {0} but'
                               ' found {1}'.format(element.name, key))

            if strict and isinstance(schema, dict):
                for key in value.keys():
                    if key not in schema:
                        raise exceptions.DSLParsingFormatException(
                            1, '{0} is not permitted'.format(key))

            if (isinstance(schema, elements.List) and
                    not isinstance(value, list)):
                raise exceptions.DSLParsingFormatException(
                    1, 'Expected list value for {0} but found {1}'
                       .format(element.name, value))

            if (isinstance(schema, elements.Leaf) and
                    not isinstance(value, schema.type)):
                if isinstance(schema.type, tuple):
                    type_name = [t.__name__ for t in schema.type]
                else:
                    type_name = schema.type.__name__
                raise exceptions.DSLParsingFormatException(
                    1, 'Expected {0} value for {1} but found {2}'
                       .format(type_name,
                               element.name,
                               value))
        if value is not None:
            if isinstance(element.schema, list):
                validated = False
                last_error = None
                for schema_item in element.schema:
                    try:
                        validate_schema(schema_item)
                    except exceptions.DSLParsingFormatException as e:
                        last_error = e
                    else:
                        validated = True
                        break
                if not validated:
                    if not last_error:
                        raise exceptions.DSLParsingFormatException(
                            1, 'Invalid list schema')
                    else:
                        raise last_error
            else:
                validate_schema(element.schema)

        element.validate(**required_args)

    @staticmethod
    def _parse_element(element, required_args):
        value = element.parse(**required_args)
        element.value = value
        element.provided = element.calculate_provided(**required_args)

    @staticmethod
    def _extract_element_requirements(element, context):
        required_args = {}
        for required_type, requirements in element.requires.items():
            requirements = [Requirement(r) if isinstance(r, basestring)
                            else r for r in requirements]
            if not requirements:
                # only set required type as a logical dependency
                pass
            elif required_type == 'inputs':
                for input in requirements:
                    if input.name not in context.inputs and input.required:
                        raise exceptions.DSLParsingFormatException(
                            1, 'Missing required input: {0}'.format(
                                input.name))
                    required_args[input.name] = context.inputs.get(input.name)
            else:
                if required_type == 'self':
                    required_type = type(element)
                required_type_elements = context.element_type_to_elements.get(
                    required_type, [])
                for requirement in requirements:
                    result = []
                    for required_element in required_type_elements:
                        if requirement.predicate and not requirement.predicate(
                                element, required_element):
                            continue
                        if requirement.parsed:
                            result.append(required_element.value)
                        else:
                            if (requirement.name not in
                                    required_element.provided):
                                if requirement.required:
                                    raise exceptions.DSLParsingFormatException(
                                        1, 'Missing required value')
                                else:
                                    continue
                            result.append(required_element.provided[
                                requirement.name])

                    if len(result) != 1 and not requirement.multiple_results:
                        if requirement.required:
                            raise exceptions.DSLParsingFormatException(
                                1, 'Expected exactly one result for '
                                   'requirement: {0}'
                                   .format(requirement.name))
                        else:
                            result = [None]

                    if not requirement.multiple_results:
                        result = result[0]
                    required_args[requirement.name] = result

        return required_args

    def parse(self,
              value,
              element_cls,
              element_name='root',
              inputs=None,
              strict=True):
        context = self._init_element_context(
            value=value,
            element_cls=element_cls,
            element_name=element_name,
            inputs=inputs)
        self._iterate_elements(context, strict=strict)
        return context.root_element.value


class Context(object):

    def __init__(self, parser, inputs):
        self.parser = parser
        self.inputs = inputs or {}
        self._root_element = None
        self.element_tree = nx.DiGraph()
        self.element_graph = nx.DiGraph()
        self.element_type_to_elements = {}

    @property
    def root_element(self):
        return self._root_element

    @root_element.setter
    def root_element(self, value):
        self._root_element = value

    def add_element(self, element, parent=None):
        element_type = type(element)
        if element_type not in self.element_type_to_elements:
            self.element_type_to_elements[element_type] = []
        self.element_type_to_elements[element_type].append(element)

        self.element_tree.add_node(element)
        if parent:
            self.element_tree.add_edge(parent, element)
        else:
            self.root_element = element

    def calculate_element_graph(self):
        self.element_graph = nx.DiGraph(self.element_tree)
        for element_type, _elements in self.element_type_to_elements.items():
            requires = element_type.requires
            for requirement, requirement_values in requires.items():
                requirement_values = [
                    Requirement(r) if isinstance(r, basestring)
                    else r for r in requirement_values]
                if requirement == 'inputs':
                    continue
                if requirement == 'self':
                    requirement = element_type
                dependencies = self.element_type_to_elements.get(
                    requirement, [])
                for dependency in dependencies:
                    for element in _elements:
                        predicates = [r.predicate for r in requirement_values
                                      if r.predicate is not None]
                        add_dependency = not predicates or all([
                            predicate(element, dependency)
                            for predicate in predicates])
                        if add_dependency:
                            self.element_graph.add_edge(element, dependency)
        # we reverse the graph because only netorkx 1.9.1 has the reverse
        # flag in the topological sort function, it is only used by it
        # so this should be good
        self.element_graph.reverse(copy=False)

    def elements_graph_topological_sort(self):
        try:
            return nx.topological_sort(self.element_graph)
        except nx.NetworkXUnfeasible:
            # Cycle detected
            cycle = nx.recursive_simple_cycles(self.element_graph)[0]
            names = [e.name for e in cycle]
            names.append(names[0])
            ex = exceptions.DSLParsingLogicException(
                100, 'Failed parsing. Circular dependency detected: {0}'
                     .format(' --> '.join(names)))
            ex.circular_dependency = names
            raise ex

    def child_elements_iter(self, element):
        return self.element_tree.successors_iter(element)

    def ancestors_iter(self, element):
        current_element = element
        while True:
            predecessors = self.element_tree.predecessors(current_element)
            if not predecessors:
                return
            if len(predecessors) > 1:
                raise exceptions.DSLParsingFormatException(
                    1, 'More than 1 parent found for {0}'
                       .format(element))
            current_element = predecessors[0]
            yield current_element

    def descendants(self, element):
        return nx.descendants(self.element_tree, element)
