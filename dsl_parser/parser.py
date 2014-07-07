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

BLUEPRINT = 'blueprint'
IMPORTS = 'imports'
TYPES = 'types'
TYPE_IMPLEMENTATIONS = 'type_implementations'
PLUGINS = 'plugins'
INTERFACES = 'interfaces'
SOURCE_INTERFACES = 'source_interfaces'
TARGET_INTERFACES = 'target_interfaces'
WORKFLOWS = 'workflows'
RELATIONSHIPS = 'relationships'
RELATIONSHIP_IMPLEMENTATIONS = 'relationship_implementations'
PROPERTIES = 'properties'
TYPE_HIERARCHY = 'type_hierarchy'

HOST_TYPE = 'cloudify.types.host'
DEPENDS_ON_REL_TYPE = 'cloudify.relationships.depends_on'
CONTAINED_IN_REL_TYPE = 'cloudify.relationships.contained_in'
CONNECTED_TO_REL_TYPE = 'cloudify.relationships.connected_to'
PLUGIN_INSTALLER_PLUGIN = 'plugin_installer'
AGENT_INSTALLER_PLUGIN = "worker_installer"
WINDOWS_PLUGIN_INSTALLER_PLUGIN = 'windows_plugin_installer'
WINDOWS_AGENT_INSTALLER_PLUGIN = "windows_agent_installer"


PLUGINS_TO_INSTALL_EXCLUDE_LIST = {PLUGIN_INSTALLER_PLUGIN,
                                   WINDOWS_PLUGIN_INSTALLER_PLUGIN}
MANAGEMENT_PLUGINS_TO_INSTALL_EXCLUDE_LIST \
    = {PLUGIN_INSTALLER_PLUGIN,
       AGENT_INSTALLER_PLUGIN, WINDOWS_PLUGIN_INSTALLER_PLUGIN,
       WINDOWS_AGENT_INSTALLER_PLUGIN}

import os
import copy
import contextlib
import re
from urllib import pathname2url
from urllib2 import urlopen, URLError
from collections import OrderedDict

import yaml
from jsonschema import validate, ValidationError
from yaml.parser import ParserError

from schemas import DSL_SCHEMA, IMPORTS_SCHEMA


from collections import namedtuple
OpDescriptor = namedtuple('OpDescriptor', [
    'plugin', 'op_struct', 'name'])


def parse_from_path(dsl_file_path, alias_mapping_dict=None,
                    alias_mapping_url=None, resources_base_url=None):
    with open(dsl_file_path, 'r') as f:
        dsl_string = f.read()
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url,
                  resources_base_url, dsl_file_path)


def parse_from_url(dsl_url, alias_mapping_dict=None, alias_mapping_url=None,
                   resources_base_url=None):
    with contextlib.closing(urlopen(dsl_url)) as f:
        dsl_string = f.read()
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url,
                  resources_base_url, dsl_url)


def parse(dsl_string, alias_mapping_dict=None, alias_mapping_url=None,
          resources_base_url=None):
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url,
                  resources_base_url)


def _get_alias_mapping(alias_mapping_dict, alias_mapping_url):
    alias_mapping = {}
    if alias_mapping_url is not None:
        with contextlib.closing(urlopen(alias_mapping_url)) as f:
            alias_mapping_string = f.read()
        alias_mapping = dict(alias_mapping.items() +
                             _load_yaml(alias_mapping_string,
                                        'Failed to parse alias-mapping')
                             .items())
    if alias_mapping_dict is not None:
        alias_mapping = dict(alias_mapping.items() +
                             alias_mapping_dict.items())
    return alias_mapping


def _dsl_location_to_url(dsl_location, alias_mapping, resources_base_url):
    dsl_location = _apply_alias_mapping_if_available(dsl_location,
                                                     alias_mapping)
    if dsl_location is not None:
        dsl_location = _get_resource_location(dsl_location, resources_base_url)
        if dsl_location is None:
            ex = DSLParsingLogicException(30, 'Failed on converting dsl '
                                              'location to url - no suitable '
                                              'location found '
                                              'for dsl {0}'
                                              .format(dsl_location))
            ex.failed_import = dsl_location
            raise ex
    return dsl_location


def _load_yaml(yaml_stream, error_message):
    try:
        parsed_dsl = yaml.safe_load(yaml_stream)
    except ParserError, ex:
        raise DSLParsingFormatException(-1, '{0}: Illegal yaml; {1}'
                                        .format(error_message, ex))
    if parsed_dsl is None:
        raise DSLParsingFormatException(0, '{0}: Empty yaml'
                                        .format(error_message))
    return parsed_dsl


def _create_plan_management_plugins(processed_nodes):
    management_plugins = []
    management_plugin_names = set()
    for node in processed_nodes:
        if "management_plugins_to_install" in node:
            for management_plugin in node['management_plugins_to_install']:
                if management_plugin['name'] not in management_plugin_names:
                    management_plugins.append(management_plugin)
                    management_plugin_names.add(management_plugin['name'])
    return management_plugins


def _create_plan_workflow_plugins(workflows, plugins):
    workflow_plugins = []
    workflow_plugin_names = set()
    for workflow, op_struct in workflows.items():
        if op_struct['plugin'] not in workflow_plugin_names:
            plugin_name = op_struct['plugin']
            workflow_plugins.append(plugins[plugin_name])
            workflow_plugin_names.add(plugin_name)
    return workflow_plugins


def _parse(dsl_string, alias_mapping_dict, alias_mapping_url,
           resources_base_url, dsl_location=None):
    alias_mapping = _get_alias_mapping(alias_mapping_dict, alias_mapping_url)

    parsed_dsl = _load_yaml(dsl_string, 'Failed to parse DSL')

    if dsl_location:
        dsl_location = _dsl_location_to_url(dsl_location, alias_mapping,
                                            resources_base_url)
    combined_parsed_dsl = _combine_imports(parsed_dsl, alias_mapping,
                                           dsl_location, resources_base_url)

    _validate_dsl_schema(combined_parsed_dsl)

    blueprint = combined_parsed_dsl[BLUEPRINT]
    app_name = blueprint['name']

    nodes = blueprint['nodes']
    _validate_no_duplicate_nodes(nodes)

    top_level_relationships = _process_relationships(combined_parsed_dsl)

    node_names_set = {node['name'] for node in nodes}
    type_impls = _get_dict_prop(combined_parsed_dsl, TYPE_IMPLEMENTATIONS)\
        .copy()
    relationship_impls = _get_dict_prop(combined_parsed_dsl,
                                        RELATIONSHIP_IMPLEMENTATIONS).copy()

    plugins = _get_dict_prop(combined_parsed_dsl, PLUGINS)
    processed_plugins = {name: _process_plugin(plugin, name)
                         for (name, plugin) in plugins.items()}

    processed_nodes = map(lambda node: _process_node(
        node, combined_parsed_dsl,
        top_level_relationships, node_names_set, type_impls,
        relationship_impls, processed_plugins), nodes)

    _post_process_nodes(processed_nodes,
                        _get_dict_prop(combined_parsed_dsl, TYPES),
                        _get_dict_prop(combined_parsed_dsl, RELATIONSHIPS),
                        processed_plugins,
                        type_impls,
                        relationship_impls,
                        node_names_set)

    processed_workflows = _process_workflows(
        combined_parsed_dsl.get(WORKFLOWS, {}),
        processed_plugins)
    workflow_plugins_to_install = _create_plan_workflow_plugins(
        processed_workflows,
        processed_plugins)

    plan_management_plugins = _create_plan_management_plugins(processed_nodes)

    plan = {
        'name': app_name,
        'nodes': processed_nodes,
        RELATIONSHIPS: top_level_relationships,
        WORKFLOWS: processed_workflows,
        'management_plugins_to_install': plan_management_plugins,
        'workflow_plugins_to_install': workflow_plugins_to_install
    }

    return plan


def _post_process_nodes(processed_nodes, types, relationships, plugins,
                        type_impls, relationship_impls, node_names):
    node_name_to_node = {node['id']: node for node in processed_nodes}

    depends_on_rel_types = _build_family_descendants_set(
        relationships, DEPENDS_ON_REL_TYPE)
    contained_in_rel_types = _build_family_descendants_set(
        relationships, CONTAINED_IN_REL_TYPE)
    connected_to_rel_types = _build_family_descendants_set(
        relationships, CONNECTED_TO_REL_TYPE)
    for node in processed_nodes:
        _post_process_node_relationships(node,
                                         node_name_to_node,
                                         plugins,
                                         contained_in_rel_types,
                                         connected_to_rel_types,
                                         depends_on_rel_types,
                                         relationships)
        node[TYPE_HIERARCHY] = _create_type_hierarchy(node['type'], types)

    # set host_id property to all relevant nodes
    host_types = _build_family_descendants_set(types, HOST_TYPE)
    for node in processed_nodes:
        host_id = _extract_node_host_id(node, node_name_to_node, host_types,
                                        contained_in_rel_types)
        if host_id:
            node['host_id'] = host_id

    # set plugins_to_install property for nodes
    # set management_plugins_to_install property nodes
    for node in processed_nodes:
        if node['type'] in host_types:
            plugins_to_install = {}
            management_plugins_to_install = {}
            for another_node in processed_nodes:
                # going over all other nodes, to accumulate plugins
                # from different nodes whose host is the current node
                if 'host_id' in another_node and \
                        another_node['host_id'] == node['id'] and \
                        PLUGINS in another_node:
                    # ok to override here since we assume it is the same plugin
                    for plugin_name, plugin_obj in \
                            another_node[PLUGINS].iteritems():
                        # only wish to add agent plugins, and only if they're
                        # not in the excluded plugins list
                        if plugin_obj['agent_plugin'] == 'true' and \
                                plugin_obj['name'] not in \
                                PLUGINS_TO_INSTALL_EXCLUDE_LIST:
                            plugins_to_install[plugin_name] = plugin_obj
                        if plugin_obj['manager_plugin'] == 'true' and \
                                plugin_obj['name'] not in \
                                MANAGEMENT_PLUGINS_TO_INSTALL_EXCLUDE_LIST:
                            management_plugins_to_install[plugin_name] \
                                = plugin_obj
            node['plugins_to_install'] = plugins_to_install.values()
            node['management_plugins_to_install'] \
                = management_plugins_to_install.values()

    _validate_agent_plugins_on_host_nodes(processed_nodes)
    _validate_type_impls(type_impls)
    _validate_relationship_impls(relationship_impls)


def _create_type_hierarchy(type_name, types):
    """
    Creates node types hierarchy as list where the last type in the list is
    the actual node type.
    """
    current_type = types[type_name]
    if 'derived_from' in current_type:
        parent_type_name = current_type['derived_from']
        types_hierarchy = _create_type_hierarchy(parent_type_name, types)
        types_hierarchy.append(type_name)
        return types_hierarchy
    return [type_name]


def _post_process_node_relationships(node,
                                     node_name_to_node,
                                     plugins,
                                     contained_in_rel_types,
                                     connected_to_rel_types,
                                     depends_on_rel_type,
                                     relationships):
    contained_in_relationships = []
    if RELATIONSHIPS in node:
        for relationship in node[RELATIONSHIPS]:
            target_node = node_name_to_node[relationship['target_id']]
            _process_node_relationships_operations(
                relationship, 'source_interfaces', 'source_operations', node,
                plugins)
            _process_node_relationships_operations(
                relationship, 'target_interfaces', 'target_operations',
                target_node, plugins)
            _add_base_type_to_relationship(relationship,
                                           contained_in_rel_types,
                                           connected_to_rel_types,
                                           depends_on_rel_type,
                                           contained_in_relationships)
            relationship[TYPE_HIERARCHY] = _create_type_hierarchy(
                relationship['type'], relationships)

    if len(contained_in_relationships) > 1:
        ex = DSLParsingLogicException(
            112, 'Node {0} has more than one relationship that is derived'
                 ' from {1} relationship. Found: {2}'
                 .format(node['name'],
                         CONTAINED_IN_REL_TYPE,
                         contained_in_relationships))
        ex.relationship_types = contained_in_relationships
        raise ex


# used in multi_instance
def _add_base_type_to_relationship(relationship,
                                   contained_in_rel_types,
                                   connected_to_rel_types,
                                   depends_on_rel_types,
                                   contained_in_relationships):
    base = 'undefined'
    rel_type = relationship['type']
    if rel_type in contained_in_rel_types:
        base = 'contained'
        contained_in_relationships.append(rel_type)
    elif rel_type in connected_to_rel_types:
        base = 'connected'
    elif rel_type in depends_on_rel_types:
        base = 'depends'
    relationship['base'] = base


pattern = re.compile("(.+)\[(\d+)\]")


def _expand(context_properties, node_properties, node_id, operation_name):

    def raise_exception(property_path):
        ex = DSLParsingLogicException(
            104, 'Mapped property {0} does not exist in the '
                 'context node properties {1} (node {2}, '
                 'operation {3})'.format(property_path,
                                         node_properties,
                                         node_id,
                                         operation_name))
        ex.property_name = property_path
        raise ex

    if not context_properties:
        return None
    result = {}
    for key, value in context_properties.items():
        if type(value) == dict:
            if len(value) == 1 and value.keys()[0] == 'get_property':
                property_path = value.values()[0]
                current_properties_level = node_properties
                for property_segment in property_path.split('.'):
                    match = pattern.match(property_segment)
                    if match:
                        index = int(match.group(2))
                        property_name = match.group(1)
                        if property_name not in current_properties_level:
                            raise_exception(property_path)
                        if type(current_properties_level[property_name]) != \
                                list:
                            raise_exception(property_path)
                        current_properties_level = \
                            current_properties_level[property_name][index]
                    else:
                        if property_segment not in current_properties_level:
                            raise_exception(property_path)
                        current_properties_level = \
                            current_properties_level[property_segment]
                    result[key] = current_properties_level
            else:
                if 'get_property' in value:
                    raise DSLParsingLogicException(
                        105, "Additional properties are not allowed when "
                             "using 'get_property' (node {0}, operation {1}, "
                             "property {2})".format(key,
                                                    node_id, operation_name))
                result[key] = _expand(value, node_properties, node_id,
                                      operation_name)
        else:
            result[key] = value
    return result


def _process_context_operations(partial_error_message, interfaces, plugins,
                                node, error_code):
    operations = {}
    for interface_name, interface in interfaces.items():
        operation_mapping_context = \
            _extract_plugin_names_and_operation_mapping_from_interface(
                interface,
                plugins,
                error_code,
                'In interface {0} {1}'.format(interface_name,
                                              partial_error_message))
        _validate_no_duplicate_operations(operation_mapping_context,
                                          interface_name, node['id'],
                                          node['type'])
        # for operation_name, plugin_name, operation_mapping, \
        #         operation_properties in operation_mapping_context:
        for op_descriptor in operation_mapping_context:
            if op_descriptor.plugin is not None:
                op_struct = op_descriptor.op_struct
                plugin_name = op_descriptor.op_struct['plugin']
                operation_name = op_descriptor.name
                operation_properties = _expand(
                    op_descriptor.op_struct.get('properties'),
                    _get_dict_prop(node, 'properties'),
                    node['id'],
                    operation_name)
                node[PLUGINS][plugin_name] = op_descriptor.plugin
                op_struct = op_struct.copy()
                if operation_properties is not None:
                    op_struct['properties'] = operation_properties
                if operation_name in operations:
                    # Indicate this implicit operation name needs to be
                    # removed as we can only
                    # support explicit implementation in this case
                    operations[operation_name] = None
                else:
                    operations[operation_name] = op_struct
                operations['{0}.{1}'.format(interface_name,
                                            operation_name)] = op_struct

    return dict((operation, op_struct) for operation, op_struct in
                operations.iteritems() if op_struct is not None)


def _process_node_relationships_operations(relationship,
                                           interfaces_attribute,
                                           operations_attribute,
                                           node_for_plugins,
                                           plugins):
    if interfaces_attribute in relationship:
        partial_error_message = 'in relationship of type {0} in node {1}'\
                                .format(relationship['type'],
                                        node_for_plugins['id'])

        operations = _process_context_operations(
            partial_error_message,
            relationship[interfaces_attribute],
            plugins, node_for_plugins, 19)

        relationship[operations_attribute] = operations


def _extract_plugin_names_and_operation_mapping_from_interface(
        interface,
        plugins,
        error_code,
        partial_error_message):
    plugin_names = plugins.keys()
    result = []
    for operation in interface:
        op_descriptor = \
            _extract_plugin_name_and_operation_mapping_from_operation(
                plugins, plugin_names, operation, error_code,
                partial_error_message)
        result.append(op_descriptor)
    return result


def _validate_type_impls(type_impls):
    for impl_name, impl_content in type_impls.iteritems():
        node_ref = impl_content['node_ref']
        ex = \
            DSLParsingLogicException(
                110, '\'{0}\' type implementation has a reference to a '
                     'node which does not exist named \'{1}\''.
                format(impl_name, node_ref))
        ex.implementation = impl_name
        ex.node_ref = node_ref
        raise ex


def _validate_relationship_impls(relationship_impls):
    for impl_name, impl_content in relationship_impls.iteritems():
        source_node_ref = impl_content['source_node_ref']
        target_node_ref = impl_content['target_node_ref']
        ex = \
            DSLParsingLogicException(
                111, '\'{0}\' relationship implementation between \'{1}->{'
                     '2}\' is not mapped to any matching node relationship'.
                format(impl_name, source_node_ref, target_node_ref))
        ex.implementation = impl_name
        ex.source_node_ref = source_node_ref
        raise ex


def _validate_agent_plugins_on_host_nodes(processed_nodes):
    for node in processed_nodes:
        if 'host_id' not in node and PLUGINS in node:
            for plugin in node[PLUGINS].itervalues():
                if plugin['agent_plugin'] == 'true':
                    raise DSLParsingLogicException(
                        24, "node {0} has no relationship which makes it "
                            "contained within a host and it has an agent "
                            "plugin named {1}, agent plugins must be "
                            "installed on a host".format(node['id'],
                                                         plugin['name']))


def _build_family_descendants_set(types_dict, derived_from):
    return {type_name for type_name in types_dict.iterkeys()
            if _is_derived_from(type_name, types_dict, derived_from)}


def _is_derived_from(type_name, types, derived_from):
    if type_name == derived_from:
        return True
    elif 'derived_from' in types[type_name]:
        return _is_derived_from(types[type_name]['derived_from'], types,
                                derived_from)
    return False


# This method is applicable to both types and relationships.
# it's concerned with extracting the super types
# recursively, where the merging_func parameter is used to merge them with the
# current type
def _extract_complete_type_recursive(type_obj, type_name, dsl_container,
                                     merging_func, visited_type_names,
                                     is_relationships):
    if type_name in visited_type_names:
        visited_type_names.append(type_name)
        ex = DSLParsingLogicException(
            100, 'Failed parsing {0} {1}, Circular dependency detected: {2}'
                 .format('relationship' if is_relationships else 'type',
                         type_name, ' --> '.join(visited_type_names)))
        ex.circular_dependency = visited_type_names
        raise ex
    visited_type_names.append(type_name)
    current_level_type = copy.deepcopy(type_obj)
    # halt condition
    if 'derived_from' not in current_level_type:
        return current_level_type

    super_type_name = current_level_type['derived_from']
    if super_type_name not in dsl_container:
        raise DSLParsingLogicException(
            14, 'Missing definition for {0} {1} which is declared as derived '
                'by {0} {2}'.format(
                    'relationship' if is_relationships else 'type',
                    super_type_name,
                    type_name))

    super_type = dsl_container[super_type_name]
    complete_super_type = _extract_complete_type_recursive(
        super_type, super_type_name, dsl_container, merging_func,
        visited_type_names, is_relationships)
    return merging_func(complete_super_type, current_level_type)


def _process_relationships(combined_parsed_dsl):
    processed_relationships = {}
    if RELATIONSHIPS not in combined_parsed_dsl:
        return processed_relationships

    relationships = combined_parsed_dsl[RELATIONSHIPS]

    for rel_name, rel_obj in relationships.iteritems():
        complete_rel_obj = _extract_complete_type_recursive(
            rel_obj, rel_name, relationships,
            _rel_inheritance_merging_func, [], True)

        plugins = _get_dict_prop(combined_parsed_dsl, PLUGINS)
        _validate_relationship_fields(complete_rel_obj, plugins, rel_name)
        complete_rel_obj_copy = copy.deepcopy(complete_rel_obj)
        processed_relationships[rel_name] = complete_rel_obj_copy
        processed_relationships[rel_name]['name'] = rel_name
    return processed_relationships


def _validate_relationship_fields(rel_obj, plugins, rel_name):
    for interfaces in [SOURCE_INTERFACES, TARGET_INTERFACES]:
        if interfaces in rel_obj:
            for interface_name, interface in rel_obj[interfaces].items():
                operation_mapping_context = \
                    _extract_plugin_names_and_operation_mapping_from_interface(
                        interface,
                        plugins,
                        19,
                        'Relationship: {0}'.format(rel_name))
                _validate_no_duplicate_operations(
                    operation_mapping_context, interface_name,
                    relationship_name=rel_name)


def _rel_inheritance_merging_func(complete_super_type,
                                  current_level_type,
                                  merge_properties=True):
    merged_type = current_level_type

    if merge_properties:
        merged_props_array = _merge_properties_arrays(complete_super_type,
                                                      merged_type,
                                                      PROPERTIES)
        if len(merged_props_array) > 0:
            merged_type[PROPERTIES] = merged_props_array

    # derived source and target interfaces
    for interfaces in [SOURCE_INTERFACES, TARGET_INTERFACES]:
        merged_interfaces = _merge_interface_dicts(complete_super_type,
                                                   merged_type, interfaces)
        if len(merged_interfaces) > 0:
            merged_type[interfaces] = merged_interfaces

    return merged_type


def _merge_interface_dicts(overridden, overriding, interfaces_attribute):
    if interfaces_attribute not in overridden and \
            interfaces_attribute not in overriding:
        return {}
    if interfaces_attribute not in overridden:
        return overriding[interfaces_attribute]
    if interfaces_attribute not in overriding:
        return overridden[interfaces_attribute]
    merged_interfaces = copy.deepcopy(overridden[interfaces_attribute])
    for overriding_interface, interface_obj in \
            overriding[interfaces_attribute].items():
        interface_obj_copy = copy.deepcopy(interface_obj)
        if overriding_interface not in overridden[interfaces_attribute]:
            merged_interfaces[overriding_interface] = interface_obj_copy
        else:
            merged_interfaces[overriding_interface] = _merge_interface_list(
                overridden[interfaces_attribute][overriding_interface],
                interface_obj_copy)
    return merged_interfaces


def _merge_interface_list(overridden_interface, overriding_interface):

    def op_and_op_name(op):
        if type(op) == str:
            return op, op
        key, value = op.items()[0]
        return key, op

    # OrderedDict for easier testability
    overridden = OrderedDict((x, y) for x, y in map(op_and_op_name,
                                                    overridden_interface))
    overriding = OrderedDict((x, y) for x, y in map(op_and_op_name,
                                                    overriding_interface))
    result = []
    for op_name, operation in overridden.items():
        if op_name not in overriding:
            result.append(operation)
        else:
            result.append(overriding[op_name])
    for op_name, operation in overriding.items():
        if op_name not in overridden:
            result.append(operation)
    return result


def _extract_plugin_name_and_operation_mapping_from_operation(
        plugins,
        plugin_names,
        operation,
        error_code,
        partial_error_message,
        is_workflows=False):
    properties_field_name = 'parameters' if is_workflows else 'properties'
    if type(operation) == str:
        return OpDescriptor(name=operation,
                            plugin=None,
                            op_struct=_operation_struct(
                                None,
                                None,
                                None,
                                properties_field_name))
    operation_name = operation.keys()[0]
    operation_content = operation.values()[0]
    operation_properties = None
    if type(operation_content) == str:
        operation_mapping = operation_content
    else:
        operation_mapping = operation_content['mapping']
        operation_properties = operation_content[properties_field_name]

    longest_prefix = 0
    longest_prefix_plugin_name = None
    for plugin_name in plugin_names:
        if operation_mapping.startswith('{0}.'.format(plugin_name)):
            plugin_name_length = len(plugin_name)
            if plugin_name_length > longest_prefix:
                longest_prefix = plugin_name_length
                longest_prefix_plugin_name = plugin_name
    if longest_prefix_plugin_name is not None:
        return OpDescriptor(
            name=operation_name,
            plugin=plugins[longest_prefix_plugin_name],
            op_struct=_operation_struct(
                longest_prefix_plugin_name,
                operation_mapping[longest_prefix + 1:],
                operation_properties,
                properties_field_name
            ))
    else:
        # This is an error for validation done somewhere down the
        # current stack trace
        base_error_message = 'Could not extract plugin from {2} ' + \
                             'mapping {0}, which is declared for {2} ' \
                             '{1}.'.format(
                                 operation_mapping,
                                 operation_name,
                                 'workflow' if is_workflows else 'operation')
        error_message = base_error_message + partial_error_message
        raise DSLParsingLogicException(error_code, error_message)


def _process_workflows(workflows, plugins):
    processed_workflows = {}
    plugin_names = plugins.keys()
    for name, mapping in workflows.items():
        op_descriptor = \
            _extract_plugin_name_and_operation_mapping_from_operation(
                plugins=plugins,
                plugin_names=plugin_names,
                operation={name: mapping},
                error_code=21,
                partial_error_message='',
                is_workflows=True)
        processed_workflows[name] = op_descriptor.op_struct
    return processed_workflows


def _validate_no_duplicate_nodes(nodes):
    duplicate = _validate_no_duplicate_element(nodes,
                                               lambda node: node['name'])
    if duplicate is not None:
        ex = DSLParsingLogicException(
            101, 'Duplicate node definition detected, there are {0} nodes '
                 'with name {1} defined'.format(duplicate[1], duplicate[0]))
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


def _process_node_relationships(app_name, node, node_name, node_names_set,
                                processed_node, top_level_relationships,
                                relationship_impls):
    if RELATIONSHIPS in node:
        relationships = []
        for relationship in node[RELATIONSHIPS]:
            relationship_type = relationship['type']
            relationship_type, impl_properties = \
                _get_relationship_implementation_if_exists(
                    node_name, relationship['target'], relationship_impls,
                    relationship_type, top_level_relationships)
            relationship['type'] = relationship_type
            # validating only the instance relationship values - the inherited
            # relationship values if any
            # should have been validated when the top level relationships were
            # processed.
            # validate target field (done separately since it's only available
            # in instance relationships)
            if relationship['target'] not in node_names_set:
                raise DSLParsingLogicException(
                    25, 'a relationship instance under node {0} of type {1} '
                        'declares an undefined target node {2}'
                        .format(node_name, relationship_type,
                                relationship['target']))
            if relationship['target'] == node_name:
                raise DSLParsingLogicException(
                    23, 'a relationship instance under node {0} of type {1} '
                        'illegally declares the source node as the target node'
                        .format(node_name, relationship_type))
                # merge relationship instance with relationship type
            if relationship_type not in top_level_relationships:
                raise DSLParsingLogicException(
                    26, 'a relationship instance under node {0} declares an '
                        'undefined relationship type {1}'
                        .format(node_name, relationship_type))

            relationship_complete_type = \
                top_level_relationships[relationship_type]
            complete_relationship = _rel_inheritance_merging_func(
                relationship_complete_type,
                relationship,
                merge_properties=False)
            complete_relationship[PROPERTIES] = \
                _merge_schema_and_instance_properties(
                    _get_dict_prop(relationship, PROPERTIES),
                    impl_properties,
                    _get_list_prop(relationship_complete_type, PROPERTIES),
                    '{0} node relationship \'{1}\' property is not part of '
                    'the derived relationship type properties schema',
                    '{0} node relationship does not provide a '
                    'value for mandatory  '
                    '\'{1}\' property which is '
                    'part of its relationship type schema',
                    node_name=node_name
                )
            complete_relationship['target_id'] = \
                complete_relationship['target']
            del (complete_relationship['target'])
            complete_relationship['state'] = 'reachable'
            relationships.append(complete_relationship)

        processed_node[RELATIONSHIPS] = relationships


def _get_implementation(lookup_message_str, type_name, implementations,
                        impl_category, types, err_code_ambig,
                        err_code_derive, candidate_func):
    candidates = {impl_name: impl_content for impl_name, impl_content in
                  implementations.iteritems() if
                  candidate_func(impl_content)}

    if len(candidates) > 1:
        ex = \
            DSLParsingLogicException(
                err_code_ambig, 'Ambiguous implementation of {0} {1} detected,'
                ' more than one candidate - {2}'.format(impl_category,
                                                        lookup_message_str,
                                                        candidates.keys()))
        ex.implementations = list(candidates.keys())
        raise ex

    if len(candidates) == 0:
        return None

    impl = candidates.values()[0]
    impl_name = candidates.keys()[0]
    impl_type = impl['type']
    if not _is_derived_from(impl_type, types, type_name):
        ex = \
            DSLParsingLogicException(
                err_code_derive,
                'Type of implementation {0} of {1} {2} is not equal or'
                ' derives from the node type - {3} cannot replace {4}'
                .format(impl_name, impl_category, lookup_message_str,
                        impl_type, type_name))
        ex.implementation = impl_name
        raise ex

    del implementations[impl_name]

    return impl


def _get_type_implementation_if_exists(node_name, node_type_name,
                                       type_implementations, types):

    def candidate_function(impl_content):
        return impl_content['node_ref'] == node_name

    impl = _get_implementation(node_name,
                               node_type_name,
                               type_implementations,
                               'node',
                               types,
                               103,
                               102,
                               candidate_function)
    if impl is None:
        return node_type_name, dict()

    impl_type = impl['type']

    return impl_type, _get_dict_prop(impl, 'properties')


def _get_relationship_implementation_if_exists(source_node_name,
                                               target_node_name,
                                               relationship_impls,
                                               relationship_type,
                                               relationships):
    def candidate_function(impl_content):
        return \
            impl_content['source_node_ref'] == source_node_name and \
            impl_content['target_node_ref'] == target_node_name and \
            _is_derived_from(impl_content['type'], relationships,
                             relationship_type)

    impl = _get_implementation('{0}->{1}'.format(source_node_name,
                                                 target_node_name),
                               relationship_type,
                               relationship_impls,
                               'relationship',
                               relationships,
                               108,
                               109,
                               candidate_function)

    if impl is None:
        return relationship_type, dict()

    return impl['type'], _get_dict_prop(impl, PROPERTIES)


def _validate_no_duplicate_operations(interface_operation_mappings,
                                      interface_name,
                                      node_id=None,
                                      node_type=None,
                                      relationship_name=None):
    operation_names = set()
    for op_descriptor in interface_operation_mappings:
        operation_name = op_descriptor.name
        if operation_name in operation_names:
            error_message = 'Duplicate operation {0} found in interface {1} '\
                            .format(operation_name, interface_name)
            if node_id is not None:
                error_message += ' in node {0} '.format(node_id)
            if node_type is not None:
                error_message += ' node type {0}'.format(node_type)
            if relationship_name is not None:
                error_message += ' relationship name {0}'.format(
                    relationship_name)
            raise DSLParsingLogicException(20, error_message)
        operation_names.add(operation_name)


def _operation_struct(plugin_name, operation_mapping, operation_properties,
                      properties_field_name):
    result = {'plugin': plugin_name, 'operation': operation_mapping}
    if operation_properties:
        result[properties_field_name] = operation_properties
    return result


def _process_node(node, parsed_dsl,
                  top_level_relationships, node_names_set, type_impls,
                  relationship_impls, plugins):
    declared_node_type_name = node['type']
    node_name = node['name']
    app_name = parsed_dsl[BLUEPRINT]['name']
    processed_node = {'name': node_name,
                      'id': node_name,
                      'declared_type': declared_node_type_name}

    # handle types
    if TYPES not in parsed_dsl or declared_node_type_name not in \
            parsed_dsl[TYPES]:
        err_message = 'Could not locate node type: {0}; existing types: {1}'\
                      .format(declared_node_type_name,
                              parsed_dsl[TYPES].keys() if
                              TYPES in parsed_dsl else 'None')
        raise DSLParsingLogicException(7, err_message)

    node_type_name, impl_properties = \
        _get_type_implementation_if_exists(
            node_name, declared_node_type_name,
            type_impls,
            parsed_dsl[TYPES])
    processed_node['type'] = node_type_name

    node_type = parsed_dsl[TYPES][node_type_name]
    complete_node_type = _extract_complete_node_type(node_type, node_type_name,
                                                     parsed_dsl, node,
                                                     impl_properties)
    processed_node[PROPERTIES] = complete_node_type[PROPERTIES]
    processed_node[PLUGINS] = {}
    # handle plugins and operations
    if INTERFACES in complete_node_type:
        partial_error_message = 'in node {0} of type {1}'\
            .format(processed_node['id'], processed_node['type'])
        operations = _process_context_operations(
            partial_error_message,
            complete_node_type[INTERFACES],
            plugins,
            processed_node, 10)

        processed_node['operations'] = operations

    # handle relationships
    _process_node_relationships(app_name, node, node_name, node_names_set,
                                processed_node, top_level_relationships,
                                relationship_impls)

    processed_node[PROPERTIES]['cloudify_runtime'] = {}

    processed_node['instances'] = node['instances'] \
        if 'instances' in node else {'deploy': 1}

    return processed_node


def _extract_node_host_id(processed_node, node_name_to_node, host_types,
                          contained_in_rel_types):
    if processed_node['type'] in host_types:
        return processed_node['id']
    else:
        if RELATIONSHIPS in processed_node:
            for rel in processed_node[RELATIONSHIPS]:
                if rel['type'] in contained_in_rel_types:
                    return _extract_node_host_id(
                        node_name_to_node[rel['target_id']],
                        node_name_to_node,
                        host_types,
                        contained_in_rel_types)


def _process_plugin(plugin, plugin_name):
    cloudify_plugins = (
        'cloudify.plugins.agent_plugin',
        'cloudify.plugins.remote_plugin',
        'cloudify.plugins.manager_plugin')
    if plugin_name in cloudify_plugins or \
            plugin_name == 'cloudify.plugins.plugin':
        return plugin
    # 'cloudify.plugins.plugin'
    if plugin['derived_from'] not in cloudify_plugins:
        # TODO: consider changing the below exception to type
        # DSLParsingFormatException..?
        raise DSLParsingLogicException(
            18, 'plugin {0} has an illegal "derived_from" value {1}; value '
                'must be either {2} or {3}'.format(
                    plugin_name,
                    plugin['derived_from'],
                    'cloudify.plugins.agent_plugin',
                    'cloudify.plugins.remote_plugin',
                    'cloudify.plugins.manager_plugin'))
    processed_plugin = copy.deepcopy(plugin.get(PROPERTIES, {}))
    processed_plugin['name'] = plugin_name
    processed_plugin['agent_plugin'] = \
        str(plugin['derived_from'] == 'cloudify.plugins.agent_plugin').lower()
    processed_plugin['manager_plugin'] = \
        str(plugin['derived_from']
            == 'cloudify.plugins.manager_plugin').lower()

    return processed_plugin


def _merge_sub_list(overridden_dict, overriding_dict, sub_list_key):
    def _get_named_list_dict(sub_list):
        return {entry['name']: entry for entry in sub_list}.items()

    overridden_sub_list = _get_list_prop(overridden_dict, sub_list_key)
    overriding_sub_list = _get_list_prop(overriding_dict, sub_list_key)
    name_to_list_entry = dict(_get_named_list_dict(overridden_sub_list) +
                              _get_named_list_dict(overriding_sub_list))
    return name_to_list_entry.values()


def _merge_sub_dicts(overridden_dict, overriding_dict, sub_dict_key):
    overridden_sub_dict = _get_dict_prop(overridden_dict, sub_dict_key)
    overriding_sub_dict = _get_dict_prop(overriding_dict, sub_dict_key)
    return dict(overridden_sub_dict.items() + overriding_sub_dict.items())


def _merge_properties_arrays(overridden, overriding,
                             properties_attribute):
    overridden_properties_schema = _get_list_prop(overridden,
                                                  properties_attribute)
    overriding_properties_schema = _get_list_prop(overriding,
                                                  properties_attribute)

    def prop_array_to_dict(properties_schema):
        result = {}
        for property_element in properties_schema:
            if type(property_element) == str:
                result[property_element] = property_element
            else:
                result[property_element.keys()[0]] = property_element
        return result.items()

    merged_properties_dict = \
        dict(prop_array_to_dict(overridden_properties_schema) +
             prop_array_to_dict(overriding_properties_schema))
    return merged_properties_dict.values()


def _extract_complete_node_type(dsl_type, dsl_type_name, parsed_dsl, node,
                                impl_properties):
    def types_and_node_inheritance_common_merging_func(complete_super_type,
                                                       merged_type):
        # derive interfaces
        merged_type[INTERFACES] = _merge_interface_dicts(complete_super_type,
                                                         merged_type,
                                                         INTERFACES)
        return merged_type

    def types_inheritance_merging_func(complete_super_type,
                                       current_level_type):
        merged_type = current_level_type
        # derive properties, need special handling as node properties and type
        # properties are not of the same format
        merged_type[PROPERTIES] = _merge_properties_arrays(complete_super_type,
                                                           merged_type,
                                                           PROPERTIES)

        types_and_node_inheritance_common_merging_func(complete_super_type,
                                                       merged_type)

        return merged_type

    complete_type = _extract_complete_type_recursive(
        dsl_type, dsl_type_name,
        parsed_dsl[TYPES],
        types_inheritance_merging_func, [], False)

    complete_node = types_and_node_inheritance_common_merging_func(
        complete_type,
        copy.deepcopy(node))

    complete_node[PROPERTIES] = _merge_schema_and_instance_properties(
        _get_dict_prop(node, PROPERTIES),
        impl_properties,
        _get_list_prop(complete_type, PROPERTIES),
        '{0} node \'{1}\' property is not part of the derived'
        ' type properties schema',
        '{0} node does not provide a '
        'value for mandatory  '
        '\'{1}\' property which is '
        'part of its type schema',
        node_name=node['name']
    )

    return complete_node


def _merge_schema_and_instance_properties(
        instance_properties,
        impl_properties,
        schema_properties,
        undefined_property_error_message,
        missing_property_error_message,
        node_name):

    instance_properties = dict(instance_properties.items() +
                               impl_properties.items())
    # Convert type schema props to prop dictionary
    complete_properties_schema = schema_properties
    complete_properties = {}
    for property_element in complete_properties_schema:
        if type(property_element) == str:
            complete_properties[property_element] = None
        else:
            complete_properties[property_element.keys()[0]] = \
                property_element.values()[0]

    for key in instance_properties.iterkeys():
        if key not in complete_properties:
            ex = DSLParsingLogicException(
                106,
                undefined_property_error_message.format(node_name, key))
            ex.property = key
            raise ex

    merged_properties = dict(complete_properties.items() +
                             instance_properties.items())

    for key, value in merged_properties.iteritems():
        if value is None:
            ex = DSLParsingLogicException(
                107,
                missing_property_error_message.format(node_name, key))
            ex.property = key
            raise ex

    return merged_properties


def _apply_ref(filename, path_context, alias_mapping, resources_base_url):
    filename = _apply_alias_mapping_if_available(filename, alias_mapping)
    ref_url = _get_resource_location(filename, resources_base_url,
                                     path_context)
    if not ref_url:
        raise DSLParsingLogicException(
            31, 'Failed on ref - Unable to locate ref {0}'.format(filename))
    try:
        with contextlib.closing(urlopen(ref_url)) as f:
            return f.read()
    except URLError:
        raise DSLParsingLogicException(
            31, 'Failed on ref - Unable to open file {0} (searched for {1})'
                .format(filename, ref_url))


def _replace_or_add_interface(merged_interfaces, interface_element):
    # locate if this interface exists in the list
    matching_interface = next((x for x in merged_interfaces if
                               _get_interface_name(x) ==
                               _get_interface_name(interface_element)), None)
    # add if not
    if matching_interface is None:
        merged_interfaces.append(interface_element)
    # replace with current interface element
    else:
        index_of_interface = merged_interfaces.index(matching_interface)
        merged_interfaces[index_of_interface] = interface_element


def _get_interface_name(interface_element):
    return interface_element if type(interface_element) == str else \
        interface_element.iterkeys().next()


def _get_list_prop(dictionary, prop_name):
    return dictionary.get(prop_name, [])


def _get_dict_prop(dictionary, prop_name):
    return dictionary.get(prop_name, {})


def _combine_imports(parsed_dsl, alias_mapping, dsl_location,
                     resources_base_url):
    def _merge_into_dict_or_throw_on_duplicate(from_dict, to_dict,
                                               top_level_key, path):
        for key, value in from_dict.iteritems():
            if key not in to_dict:
                to_dict[key] = value
            else:
                path.append(key)
                raise DSLParsingLogicException(
                    4, 'Failed on import: Could not merge {0} due to conflict '
                       'on path {1}'.format(top_level_key, ' --> '.join(path)))

    # TODO: Find a solution for top level workflows, which should be probably
    # somewhat merged with override
    merge_no_override = {INTERFACES, TYPES, PLUGINS, WORKFLOWS,
                         TYPE_IMPLEMENTATIONS, RELATIONSHIPS,
                         RELATIONSHIP_IMPLEMENTATIONS}
    merge_one_nested_level_no_override = dict()

    combined_parsed_dsl = copy.deepcopy(parsed_dsl)
    _replace_ref_with_inline_paths(combined_parsed_dsl, dsl_location,
                                   alias_mapping, resources_base_url)

    if IMPORTS not in parsed_dsl:
        return combined_parsed_dsl

    _validate_imports_section(parsed_dsl[IMPORTS], dsl_location)

    ordered_imports_list = []
    _build_ordered_imports_list(parsed_dsl, ordered_imports_list,
                                alias_mapping, dsl_location,
                                resources_base_url)
    if dsl_location:
        ordered_imports_list = ordered_imports_list[1:]

    for single_import in ordered_imports_list:
        try:
            # (note that this check is only to verify nothing went wrong in
            # the meanwhile, as we've already read
            # from all imported files earlier)
            with contextlib.closing(urlopen(single_import)) as f:
                parsed_imported_dsl = _load_yaml(
                    f, 'Failed to parse import {0}'.format(single_import))
        except URLError, ex:
            error = DSLParsingLogicException(
                13, 'Failed on import - Unable to open import url {0}; {1}'
                    .format(single_import, ex.message))
            error.failed_import = single_import
            raise error

        _replace_ref_with_inline_paths(parsed_imported_dsl, single_import,
                                       alias_mapping, resources_base_url)

        # combine the current file with the combined parsed dsl
        # we have thus far
        for key, value in parsed_imported_dsl.iteritems():
            if key == IMPORTS:  # no need to merge those..
                continue
            if key not in combined_parsed_dsl:
                # simply add this first level property to the dsl
                combined_parsed_dsl[key] = value
            else:
                if key in merge_no_override:
                    # this section will combine dictionary entries of the top
                    # level only, with no overrides
                    _merge_into_dict_or_throw_on_duplicate(
                        value, combined_parsed_dsl[key], key, [])
                elif key in merge_one_nested_level_no_override:
                    # this section will combine dictionary entries on up to one
                    # nested level, yet without overrides
                    for nested_key, nested_value in value.iteritems():
                        if nested_key not in combined_parsed_dsl[key]:
                            combined_parsed_dsl[key][nested_key] = nested_value
                        else:
                            _merge_into_dict_or_throw_on_duplicate(
                                nested_value,
                                combined_parsed_dsl[key][nested_key],
                                key, [nested_key])
                else:
                    # first level property is not white-listed for merge -
                    # throw an exception
                    raise DSLParsingLogicException(
                        3, 'Failed on import: non-mergeable field {0}'
                           .format(key))

    # clean the now unnecessary 'imports' section from the combined dsl
    if IMPORTS in combined_parsed_dsl:
        del combined_parsed_dsl[IMPORTS]
    return combined_parsed_dsl


def _replace_ref_with_inline_paths(dsl, path_context, alias_mapping,
                                   resources_base_url):
    if type(dsl) not in (list, dict):
        return

    if type(dsl) == list:
        for item in dsl:
            _replace_ref_with_inline_paths(item, path_context, alias_mapping,
                                           resources_base_url)
        return

    for key, value in dsl.iteritems():
        if key == 'ref':
            dsl[key] = _apply_ref(value, path_context, alias_mapping,
                                  resources_base_url)
        else:
            _replace_ref_with_inline_paths(value, path_context, alias_mapping,
                                           resources_base_url)


def _get_resource_location(resource_name, resources_base_url,
                           current_resource_context=None):
    # Already url format
    if resource_name.startswith('http:')\
            or resource_name.startswith('https:')\
            or resource_name.startswith('file:')\
            or resource_name.startswith('ftp:'):
        return resource_name

    # Points to an existing file
    if os.path.exists(resource_name):
        return 'file:{0}'.format(pathname2url(os.path.abspath(resource_name)))

    if current_resource_context:
        candidate_url = current_resource_context[
            :current_resource_context.rfind('/') + 1] + resource_name
        if _validate_url_exists(candidate_url):
            return candidate_url

    if resources_base_url:
        return resources_base_url + resource_name


def _validate_url_exists(url):
    try:
        with contextlib.closing(urlopen(url)):
            return True
    except URLError:
        return False


def _build_ordered_imports_list(parsed_dsl, ordered_imports_list,
                                alias_mapping, current_import,
                                resources_base_url):
    def _build_ordered_imports_list_recursive(parsed_dsl, current_import):
        if current_import is not None:
            ordered_imports_list.append(current_import)

        if IMPORTS not in parsed_dsl:
            return

        for another_import in parsed_dsl[IMPORTS]:
            another_import = _apply_alias_mapping_if_available(another_import,
                                                               alias_mapping)
            import_url = _get_resource_location(another_import,
                                                resources_base_url,
                                                current_import)
            if import_url is None:
                ex = DSLParsingLogicException(
                    13, 'Failed on import - no suitable location found for '
                        'import {0}'.format(another_import))
                ex.failed_import = another_import
                raise ex
            if import_url not in ordered_imports_list:
                try:
                    with contextlib.closing(urlopen(import_url)) as f:
                        imported_dsl = _load_yaml(
                            f, 'Failed to parse import {0} (via {1})'
                               .format(another_import, import_url))
                    _build_ordered_imports_list_recursive(imported_dsl,
                                                          import_url)
                except URLError, ex:
                    ex = DSLParsingLogicException(
                        13, 'Failed on import - Unable to open import url '
                            '{0}; {1}'.format(import_url, ex.message))
                    ex.failed_import = import_url
                    raise ex

    _build_ordered_imports_list_recursive(parsed_dsl, current_import)


def _validate_dsl_schema(parsed_dsl):
    try:
        validate(parsed_dsl, DSL_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(
            1, '{0}; Path to error: {1}'
               .format(ex.message, '.'.join((str(x) for x in ex.path))))


def _validate_imports_section(imports_section, dsl_location):
    # imports section is validated separately from the main schema since it is
    # validated for each file separately,
    # while the standard validation runs only after combining all imports
    # together
    try:
        validate(imports_section, IMPORTS_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(
            2, 'Improper "imports" section in yaml {0}; {1}; Path to error: '
               '{2}'.format(dsl_location, ex.message,
                            '.'.join((str(x) for x in ex.path))))


def _apply_alias_mapping_if_available(name, alias_mapping):
    return alias_mapping[name] if name in alias_mapping else name


class DSLParsingException(Exception):
    def __init__(self, err_code, *args):
        Exception.__init__(self, args)
        self.err_code = err_code


class DSLParsingLogicException(DSLParsingException):
    pass


class DSLParsingFormatException(DSLParsingException):
    pass
