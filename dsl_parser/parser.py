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

__author__ = 'ran'

import yaml
import copy
from jsonschema import validate, ValidationError
from yaml.parser import ParserError


def parse_from_file(dsl_file_path):
    with open(dsl_file_path, 'r') as f:
        dsl_string = f.read()
        return _parse(dsl_string, dsl_file_path)


def parse(dsl_string):
    return _parse(dsl_string)


def _parse(dsl_string, dsl_file_path=None):
    try:
        parsed_dsl = yaml.safe_load(dsl_string)
    except ParserError, ex:
        raise DSLParsingFormatException(-1, 'Failed to parse DSL: Illegal yaml file')
    if parsed_dsl is None:
        raise DSLParsingFormatException(0, 'Failed to parse DSL: Empty yaml file')

    combined_parsed_dsl = _combine_imports(parsed_dsl, dsl_file_path)

    #TODO: validate before imports? treat them dif?
    if 'imports' in combined_parsed_dsl:
        del combined_parsed_dsl['imports']
    _validate_dsl_schema(combined_parsed_dsl)

    application_template = combined_parsed_dsl['application_template']
    app_name = application_template['name']

    processed_nodes = map(lambda node: _process_node(node, combined_parsed_dsl), application_template["topology"])

    plan = {
        'name': app_name,
        'nodes': processed_nodes
    }

    return plan



def _process_node(node, parsed_dsl):
    processed_node = {}
    processed_node['id'] = '{0}.{1}'.format(parsed_dsl['application_template']['name'], node['name'])
    processed_node['type'] = node['type']

    plugins = {}
    operations = {}
    if 'types' not in parsed_dsl or node['type'] not in parsed_dsl['types']:
        err_message = 'Could not locate node type: {0}; existing types: {1}'.format(node['type'],
                                                                                    parsed_dsl['types'].keys() if
                                                                                    'types' in parsed_dsl else 'None')
        raise DSLParsingLogicException(7, err_message)

    node_type = parsed_dsl['types'][node['type']]
    complete_node_type = _extract_complete_type(node_type, parsed_dsl)

    if 'interfaces' in complete_node_type:
        if complete_node_type['interfaces'] and 'plugins' not in parsed_dsl:
            raise DSLParsingLogicException(5, 'Must provide plugins section when providing interfaces section')

        implementation_interfaces = complete_node_type['interfaces']
        for implementation_interface in implementation_interfaces:
            if type(implementation_interface) == dict: #explicit declaration
                interface_name = implementation_interface.iterkeys().next()
                plugin_name = implementation_interface.itervalues().next()
                #validate the explicit plugin declared is defined in the DSL
                if plugin_name not in parsed_dsl['plugins']:
                    raise DSLParsingLogicException(10, 'Missing definition for plugin {0} which is explicitly declared '
                                                       'to implement interface {1} for type {2}'.format(plugin_name,
                                                                                                        interface_name,
                                                                                                        node['type']))
                    #validate the explicit plugin does indeed implement the right interface
                if parsed_dsl['plugins'][plugin_name]['properties']['interface'] != interface_name:
                    raise DSLParsingLogicException(6, 'Illegal explicit plugin declaration for type {0}: the plugin {'
                                                      '1} does not implement interface {2}'.format(node['type'],
                                                                                                   plugin_name,
                                                                                                   interface_name))
            else: #implicit declaration ('autowiring')
                interface_name = implementation_interface
                plugin_name = _autowire_plugin(parsed_dsl['plugins'], interface_name, node['type'])
            plugin = parsed_dsl['plugins'][plugin_name]
            plugins[plugin_name] = plugin

            #put operations into node
            if interface_name not in parsed_dsl['interfaces']:
                raise DSLParsingLogicException(9, 'Missing interface {0} definition'.format(interface_name))
            interface = parsed_dsl['interfaces'][interface_name]
            for operation in interface['operations']:
                operations[operation] = plugin_name
                operations['{0}.{1}'.format(interface_name, operation)] = plugin_name

        processed_node['plugins'] = plugins
        processed_node['operations'] = operations

    if 'properties' in complete_node_type:
        processed_node['properties'] = complete_node_type['properties']
        if 'properties' in node:
            processed_node['properties'] = dict(processed_node['properties'].items() + node['properties'].items())
    elif 'properties' in node:
        processed_node['properties'] = node['properties']

    return processed_node


def _extract_complete_type(dsl_type, parsed_dsl):
    current_level_type = copy.deepcopy(dsl_type)
    #halt condition
    if 'derived_from' not in current_level_type:
        return current_level_type

    super_type_name = current_level_type['derived_from']
    super_type = parsed_dsl['types'][super_type_name]
    complete_super_type = _extract_complete_type(super_type, parsed_dsl)
    merged_type = current_level_type
    #derive properties
    complete_super_type_properties = _get_dict_prop(complete_super_type, 'properties')
    current_level_type_properties = _get_dict_prop(merged_type, 'properties')
    merged_properties = dict(complete_super_type_properties.items() + current_level_type_properties.items())
    merged_type['properties'] = merged_properties
    #derive interfaces
    complete_super_type_interfaces = _get_list_prop(complete_super_type, 'interfaces')
    current_level_type_interfaces = _get_list_prop(merged_type, 'interfaces')
    merged_interfaces = complete_super_type_interfaces

    for interface_element in current_level_type_interfaces:
        #we need to replace interface elements in the merged_interfaces if their interface name
        #matches this interface_element
        _replace_or_add_interface(merged_interfaces, interface_element)

    merged_type['interfaces'] = merged_interfaces

    return merged_type


def _replace_or_add_interface(merged_interfaces, interface_element):
    matching_interface = next((x for x in merged_interfaces if _get_interface_name(x) == _get_interface_name(
        interface_element)), None)
    if matching_interface is None:
        merged_interfaces.append(interface_element)
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
                        plugin_data['properties']['interface'] == interface_name]

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


def _combine_imports(parsed_dsl, dsl_file_path):
    merge_no_override = {'interfaces', 'plugins'}

    combined_parsed_dsl = copy.deepcopy(parsed_dsl)
    if 'imports' not in parsed_dsl:
        return combined_parsed_dsl

    ordered_imports_list = []
    _build_ordered_imports_list(parsed_dsl, ordered_imports_list, [], dsl_file_path)

    for single_import in ordered_imports_list:
        with open(single_import, 'r') as f:
            parsed_imported_dsl = yaml.safe_load(f)

        #combine the current file with the combined parsed dsl we have thus far
        for key, value in parsed_imported_dsl.iteritems():
            if key == 'imports':
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

    return combined_parsed_dsl


def _build_ordered_imports_list(parsed_dsl, ordered_imports_list, current_path_imports_list, current_import):
    if current_import is not None:
        current_path_imports_list.append(current_import)
        ordered_imports_list.append(current_import)

    if 'imports' not in parsed_dsl:
        return

    for another_import in parsed_dsl['imports']:
        if another_import not in ordered_imports_list:
            with open(another_import, 'r') as f:
                imported_dsl = yaml.safe_load(f)
                _build_ordered_imports_list(imported_dsl, ordered_imports_list,
                                            current_path_imports_list, another_import)
        elif another_import in current_path_imports_list:
            current_path_imports_list.append(another_import)
            ex = DSLParsingLogicException(8, 'Failed on import - Circular imports detected: {0}'.format(
                "-->".join(current_path_imports_list)))
            ex.circular_path = current_path_imports_list
            raise ex
    current_path_imports_list.pop()


def _validate_dsl_schema(parsed_dsl):
    # Schema validation is currently done using a json schema validator ( see http://json-schema.org/ ),
    # since no good YAML schema validator could be found (both for Python and at all).
    #
    # Python implementation documentation: http://python-jsonschema.readthedocs.org/en/latest/
    # A one-stop-shop for easy API explanation: http://jsonary.com/documentation/json-schema/?
    # A website which can create a schema from a given JSON automatically: http://www.jsonschema.net/#
    #   (Note: the website was not used for creating the schema below, as among other things, its syntax seems a bit
    #   different than the one used here, and should only be used as a reference)

    schema = {
        'type': 'object',
        'properties': {
            'application_template': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string'
                    },
                    'topology': {
                        'type': 'array',
                        'minItems': 1,
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'type': 'string'
                                },
                                #the below 'type' is our own "type" and not the schema's meta language
                                'type': {
                                    'type': 'string'
                                },
                                #the below 'properties' is our own "properties" and not the schema's meta language
                                'properties': {
                                    'type': 'object'
                                }
                            },
                            'required': ['name', 'type'],
                            'additionalProperties': False
                        }
                    }
                },
                'required': ['name', 'topology'],
                'additionalProperties': False
            },
            'interfaces': {
                'type': 'object',
                'patternProperties': {
                    '^': {
                        'type': 'object',
                        'properties': {
                            'operations': {
                                'type': 'array',
                                'items': {
                                    'type': 'string'
                                },
                                'uniqueItems': True,
                                'minItems': 1
                            }
                        },
                        'required': ['operations'],
                        'additionalProperties': False
                    }
                }
            },
            'plugins': {
                'type': 'object',
                'patternProperties': {
                    '^': {
                        'type': 'object',
                        'properties': {
                            #the below 'properties' is our own "properties" and not the schema's meta language
                            'properties': {
                                'type': 'object',
                                'properties': {
                                    'interface': {
                                        'type': 'string'
                                    },
                                    'url': {
                                        'type': 'string'
                                    }
                                },
                                'required': ['interface', 'url'],
                                'additionalProperties': False
                            }
                        },
                        'required': ['properties'],
                        'additionalProperties': False
                    }
                }
            },
            'types': {
                'type': 'object',
                'patternProperties': {
                    '^': {
                        'type': 'object',
                        'properties': {
                            'interfaces': {
                                'type': 'array',
                                'items': {
                                    'oneOf': [
                                        {
                                            'type': 'object',
                                            'patternProperties': {
                                                '^': {
                                                    'type': 'string'
                                                }
                                            },
                                            'maxProperties': 1,
                                            'minProperties': 1
                                        },
                                        {
                                            'type': 'string'
                                        }
                                    ],
                                    'minItems': 1
                                }
                            },
                            #the below 'properties' is our own "properties" and not the schema's meta language
                            'properties': {
                                'type': 'object'
                            },
                            'derived_from': {
                                'type': 'string'
                            }
                        },
                        'additionalProperties': False
                    }
                }
            }
        },
        'required': ['application_template'],
        'additionalProperties': False
    }

    try:
        validate(parsed_dsl, schema)
    except ValidationError, ex:
        raise DSLParsingFormatException(1, '{0}; Path to error: {1}'.format(ex.message, '.'.join((str(x) for x in ex
                                                                                                .path))))


class DSLParsingException(Exception):
    def __init__(self, err_code, *args):
        Exception.__init__(self, args)
        self.err_code = err_code


class DSLParsingLogicException(DSLParsingException):
    pass


class DSLParsingFormatException(DSLParsingException):
    pass