########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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
APPLICATION_TEMPLATE = 'application_template'
IMPORTS = 'imports'
TYPES = 'types'
PLUGINS = 'plugins'
INTERFACES = 'interfaces'
PROPERTIES = 'properties'


__author__ = 'ran'

import os
import yaml
import copy
from dsl_parser.schemas import DSL_SCHEMA, IMPORTS_SCHEMA
from jsonschema import validate, ValidationError
from yaml.parser import ParserError


filepath = os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), os.path.join('resources',
                                                                                         'alias-mappings.yaml'))
with open(filepath, 'r') as f:
    default_alias_mapping = yaml.safe_load(f.read())


def parse_from_file(dsl_file_path, alias_mapping=default_alias_mapping):
    with open(dsl_file_path, 'r') as f:
        dsl_string = f.read()
        return _parse(dsl_string, alias_mapping, dsl_file_path)


def parse(dsl_string, alias_mapping=default_alias_mapping):
    return _parse(dsl_string, alias_mapping)


def _parse(dsl_string, alias_mapping, dsl_file_path=None):
    try:
        parsed_dsl = yaml.safe_load(dsl_string)
    except ParserError, ex:
        raise DSLParsingFormatException(-1, 'Failed to parse DSL: Illegal yaml file')
    if parsed_dsl is None:
        raise DSLParsingFormatException(0, 'Failed to parse DSL: Empty yaml file')

    combined_parsed_dsl = _combine_imports(parsed_dsl, alias_mapping, dsl_file_path)

    _validate_dsl_schema(combined_parsed_dsl)

    application_template = combined_parsed_dsl[APPLICATION_TEMPLATE]
    app_name = application_template['name']

    nodes = application_template["topology"]
    _validate_no_duplicate_nodes(nodes)
    processed_nodes = map(lambda node: _process_node(node, combined_parsed_dsl), nodes)

    top_level_workflows = _process_top_level_workflows(combined_parsed_dsl['workflows'], alias_mapping) if 'workflows'\
                                                        in combined_parsed_dsl else {}

    plan = {
        'name': app_name,
        'nodes': processed_nodes,
        'workflows': top_level_workflows
    }

    return plan


def _process_top_level_workflows(workflows, alias_mapping):
    processed_workflows = {}
    for name, flow_obj in workflows.iteritems():
        if flow_obj.keys()[0] == 'ref':
            filename = flow_obj.values()[0]
            processed_workflows[name] = _apply_ref(filename, alias_mapping)
        else: #flow_obj.keys()[0] == 'radial'
            processed_workflows[name] = flow_obj.values()[0]

    return processed_workflows


def _validate_no_duplicate_nodes(nodes):
    duplicate = _validate_no_duplicate_element(nodes, lambda node: node['name'])
    if duplicate is not None:
        ex = DSLParsingLogicException(101, 'Duplicate node definition detected, there are {0} nodes with name {'
                                           '1} defined'.format(duplicate[1], duplicate[0]))
        ex.duplicate_node_name = duplicate[0]
        raise ex


def _validate_no_duplicate_element(elements, keyfunc):
    elements.sort(key=keyfunc)
    groups = []
    from itertools import groupby
    for key, group in groupby(elements, key=keyfunc):
        groups.append(list(group))
    for group in groups:
        if len(group) > 1:
            return keyfunc(group[0]), len(group)


def _process_node(node, parsed_dsl):
    node_type_name = node['type']
    processed_node = {'id': '{0}.{1}'.format(parsed_dsl[APPLICATION_TEMPLATE]['name'], node['name']),
                      'type': node_type_name}

    plugins = {}
    operations = {}
    if TYPES not in parsed_dsl or node_type_name not in parsed_dsl[TYPES]:
        err_message = 'Could not locate node type: {0}; existing types: {1}'.format(node_type_name,
                                                                                    parsed_dsl[TYPES].keys() if
                                                                                    TYPES in parsed_dsl else 'None')
        raise DSLParsingLogicException(7, err_message)

    node_type = parsed_dsl[TYPES][node_type_name]
    complete_node_type = _extract_complete_type(node_type, node_type_name, parsed_dsl)

    if INTERFACES in complete_node_type:
        if complete_node_type[INTERFACES] and PLUGINS not in parsed_dsl:
            raise DSLParsingLogicException(5, 'Must provide plugins section when providing interfaces section')

        implementation_interfaces = complete_node_type[INTERFACES]
        _validate_no_duplicate_interfaces(implementation_interfaces, node['name'])
        for implementation_interface in implementation_interfaces:
            if type(implementation_interface) == dict:
                #explicit declaration
                interface_name = implementation_interface.iterkeys().next()
                plugin_name = implementation_interface.itervalues().next()
                #validate the explicit plugin declared is defined in the DSL
                if plugin_name not in parsed_dsl[PLUGINS]:
                    raise DSLParsingLogicException(10, 'Missing definition for plugin {0} which is explicitly declared '
                                                       'to implement interface {1} for type {2}'.format(plugin_name,
                                                                                                        interface_name,
                                                                                                        node_type_name))
                    #validate the explicit plugin does indeed implement the right interface
                if parsed_dsl[PLUGINS][plugin_name][PROPERTIES]['interface'] != interface_name:
                    raise DSLParsingLogicException(6, 'Illegal explicit plugin declaration for type {0}: the plugin {'
                                                      '1} does not implement interface {2}'.format(node_type_name,
                                                                                                   plugin_name,
                                                                                                   interface_name))
            else:
                #implicit declaration ('autowiring')
                interface_name = implementation_interface
                plugin_name = _autowire_plugin(parsed_dsl[PLUGINS], interface_name, node_type_name)
            plugin = parsed_dsl[PLUGINS][plugin_name]
            plugins[plugin_name] = plugin

            #put operations into node
            if interface_name not in parsed_dsl[INTERFACES]:
                raise DSLParsingLogicException(9, 'Missing interface {0} definition'.format(interface_name))
            interface = parsed_dsl[INTERFACES][interface_name]
            for operation in interface['operations']:
                if operation in operations:
                    #Indicate this implicit operation name needs to be removed as we can only support explicit
                    # implementation in this case
                    operations[operation] = None
                else:
                    operations[operation] = plugin_name
                operations['{0}.{1}'.format(interface_name, operation)] = plugin_name

        operations = dict((operation, plugin) for operation, plugin in operations.iteritems() if plugin is not None)
        processed_node[PLUGINS] = plugins
        processed_node['operations'] = operations

    if PROPERTIES in complete_node_type:
        processed_node[PROPERTIES] = complete_node_type[PROPERTIES]
        if PROPERTIES in node:
            processed_node[PROPERTIES] = dict(processed_node[PROPERTIES].items() + node[PROPERTIES].items())
    elif PROPERTIES in node:
        processed_node[PROPERTIES] = node[PROPERTIES]

    return processed_node


def _validate_no_duplicate_interfaces(implementation_interfaces, node_name):
    duplicate = _validate_no_duplicate_element(implementation_interfaces, lambda interface: _get_interface_name(
        interface))
    if duplicate is not None:
        ex = DSLParsingLogicException(102, 'Duplicate interface definition detected on node {0}, '
                                           'interface {1} has duplicate definition'.format(node_name, duplicate[0]))
        ex.duplicate_interface_name = duplicate[0]
        ex.node_name = node_name
        raise ex


def _extract_complete_type(dsl_type, dsl_type_name, parsed_dsl):
    return _extract_complete_type_recursive(dsl_type, dsl_type_name, parsed_dsl, [])


def _extract_complete_type_recursive(dsl_type, dsl_type_name, parsed_dsl, visited_dsl_types_names):
    if dsl_type_name in visited_dsl_types_names:
        visited_dsl_types_names.append(dsl_type_name)
        ex = DSLParsingLogicException(100, 'Failed parsing type {0}, Circular dependency detected: {1}'.format(
            dsl_type_name, ' --> '.join(visited_dsl_types_names)))
        ex.circular_dependency = visited_dsl_types_names
        raise ex
    visited_dsl_types_names.append(dsl_type_name)
    current_level_type = copy.deepcopy(dsl_type)
    #halt condition
    if 'derived_from' not in current_level_type:
        return current_level_type

    super_type_name = current_level_type['derived_from']
    if super_type_name not in parsed_dsl[TYPES]:
        raise DSLParsingLogicException(14, 'Missing definition for type {0} which is declared as derived by type {1}'
                                       .format(super_type_name, dsl_type_name))

    super_type = parsed_dsl[TYPES][super_type_name]
    complete_super_type = _extract_complete_type_recursive(super_type, super_type_name, parsed_dsl,
                                                           visited_dsl_types_names)
    merged_type = current_level_type
    #derive properties
    complete_super_type_properties = _get_dict_prop(complete_super_type, PROPERTIES)
    current_level_type_properties = _get_dict_prop(merged_type, PROPERTIES)
    merged_properties = dict(complete_super_type_properties.items() + current_level_type_properties.items())
    merged_type[PROPERTIES] = merged_properties
    #derive interfaces
    complete_super_type_interfaces = _get_list_prop(complete_super_type, INTERFACES)
    current_level_type_interfaces = _get_list_prop(merged_type, INTERFACES)
    merged_interfaces = complete_super_type_interfaces

    for interface_element in current_level_type_interfaces:
        #we need to replace interface elements in the merged_interfaces if their interface name
        #matches this interface_element
        _replace_or_add_interface(merged_interfaces, interface_element)

    merged_type[INTERFACES] = merged_interfaces

    return merged_type


def _apply_ref(filename, alias_mapping):
    if filename in alias_mapping:
        filename = alias_mapping[filename]
    try:
        with open(filename, 'r') as f:
            return f.read()
    except EnvironmentError:
        raise DSLParsingLogicException(15, 'Failed on ref - Unable to open file {0}'.format(filename))


def _replace_or_add_interface(merged_interfaces, interface_element):
    #locate if this interface exists in the list
    matching_interface = next((x for x in merged_interfaces if _get_interface_name(x) == _get_interface_name(
        interface_element)), None)
    #add if not
    if matching_interface is None:
        merged_interfaces.append(interface_element)
    #replace with current interface element
    else:
        index_of_interface = merged_interfaces.index(matching_interface)
        merged_interfaces[index_of_interface] = interface_element


def _get_interface_name(interface_element):
    return interface_element if type(interface_element) == str else interface_element.iterkeys().next()


def _get_list_prop(dictionary, prop_name):
    return dictionary[prop_name] if prop_name in dictionary else []


def _get_dict_prop(dictionary, prop_name):
    return dictionary[prop_name] if prop_name in dictionary else {}


def _autowire_plugin(plugins, interface_name, type_name):
    matching_plugins = [plugin_name for plugin_name, plugin_data in plugins.items() if
                        plugin_data[PROPERTIES]['interface'] == interface_name]

    num_of_matches = len(matching_plugins)
    if num_of_matches == 0:
        raise DSLParsingLogicException(11,
                                       'Failed to find a plugin which implements interface {0} as implicitly declared '
                                       'for type {1}'.format(interface_name, type_name))

    if num_of_matches > 1:
        raise DSLParsingLogicException(12,
                                       'Ambiguous implicit declaration for interface {0} implementation under type {'
                                       '1} - Found multiple matching plugins: ({2})'.format(interface_name, type_name,
                                                                                            ','.join(matching_plugins)))

    return matching_plugins[0]


def _combine_imports(parsed_dsl, alias_mapping, dsl_file_path):
    merge_no_override = {INTERFACES, PLUGINS}

    combined_parsed_dsl = copy.deepcopy(parsed_dsl)
    if IMPORTS not in parsed_dsl:
        return combined_parsed_dsl

    _validate_imports_section(parsed_dsl[IMPORTS], dsl_file_path)

    ordered_imports_list = []
    _build_ordered_imports_list(parsed_dsl, ordered_imports_list, alias_mapping, dsl_file_path)

    for single_import in ordered_imports_list:
        try:
            #(note that this check is only to verify nothing went wrong in the meanwhile, as we've already read
            # from all imported files earlier)
            with open(single_import, 'r') as f:
                parsed_imported_dsl = yaml.safe_load(f)
        except EnvironmentError, ex:
            raise DSLParsingLogicException(13, 'Failed on import - Unable to open file {0}; {1}'.format(
                                           single_import, ex.message))

        #combine the current file with the combined parsed dsl we have thus far
        for key, value in parsed_imported_dsl.iteritems():
            if key == IMPORTS:
                continue
            if key not in combined_parsed_dsl:
                #simply add this first level property to the dsl
                combined_parsed_dsl[key] = value
            else:
                if key not in merge_no_override:
                    #first level property is not white-listed for merge - throw an exception
                    raise DSLParsingLogicException(3, 'Failed on import: non-mergeable field {0}'.format(key))
                    #going over the key-value pairs of the property we're merging
                for inner_key, inner_value in value.iteritems():
                    if inner_key not in combined_parsed_dsl[key]:
                        combined_parsed_dsl[key][inner_key] = inner_value
                    else:
                        raise DSLParsingLogicException(4, 'Failed on import: Could not merge {0} due to conflict on '
                                                          'key {1}'.format(key, inner_key))

    #clean the now unnecessary 'imports' section from the combined dsl
    if IMPORTS in combined_parsed_dsl:
        del combined_parsed_dsl[IMPORTS]
    return combined_parsed_dsl


def _build_ordered_imports_list(parsed_dsl, ordered_imports_list, alias_mapping, current_import):
    _build_ordered_imports_list_recursive(parsed_dsl, ordered_imports_list, alias_mapping, [], current_import)


def _build_ordered_imports_list_recursive(parsed_dsl, ordered_imports_list, alias_mapping, current_path_imports_list,
                                          current_import):
    def _locate_import(another_import):
        searched_locations = []
        if os.path.exists(another_import):
            return another_import
        searched_locations.append(another_import)
        if current_import is not None:
            relative_path = os.path.join(os.path.dirname(current_import), another_import)
            if os.path.exists(relative_path):
                return relative_path
            searched_locations.append(relative_path)
        raise DSLParsingLogicException(13,
                                       'Failed on import - Unable to locate import file; searched in {0}'
                                       .format(searched_locations))

    if current_import is not None:
        current_path_imports_list.append(current_import)
        ordered_imports_list.append(current_import)

    if IMPORTS not in parsed_dsl:
        if current_import is not None:
            current_path_imports_list.pop()
        return

    for another_import in parsed_dsl[IMPORTS]:
        if another_import in alias_mapping:
            another_import = alias_mapping[another_import]

        if another_import not in ordered_imports_list:
            import_path = _locate_import(another_import)
            try:
                with open(import_path, 'r') as f:
                    imported_dsl = yaml.safe_load(f)
                    _build_ordered_imports_list_recursive(imported_dsl, ordered_imports_list, alias_mapping,
                                                          current_path_imports_list, import_path)
            except EnvironmentError, ex:
                raise DSLParsingLogicException(13, 'Failed on import - Unable to open file {0}; {1}'
                                                   ''.format(import_path, ex.message))
        elif another_import in current_path_imports_list:
            current_path_imports_list.append(another_import)
            ex = DSLParsingLogicException(8, 'Failed on import - Circular imports detected: {0}'.format(
                " --> ".join(current_path_imports_list)))
            ex.circular_path = current_path_imports_list
            raise ex
    if current_import is not None:
        current_path_imports_list.pop()


def _validate_dsl_schema(parsed_dsl):
    try:
        validate(parsed_dsl, DSL_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(1, '{0}; Path to error: {1}'.format(ex.message, '.'.join((str(x) for x in ex
        .path))))


def _validate_imports_section(imports_section, filename):
    #imports section is validated separately from the main schema since it is validated for each file separately,
    #while the standard validation runs only after combining all imports together
    try:
        validate(imports_section, IMPORTS_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(2, 'Improper "imports" section in file {0}; {1}; Path to error: {2}'.format(
            filename, ex.message, '.'.join((str(x) for x in ex.path))))


class DSLParsingException(Exception):
    def __init__(self, err_code, *args):
        Exception.__init__(self, args)
        self.err_code = err_code


class DSLParsingLogicException(DSLParsingException):
    pass


class DSLParsingFormatException(DSLParsingException):
    pass