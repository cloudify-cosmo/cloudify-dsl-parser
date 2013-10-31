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
BLUEPRINT = 'blueprint'
IMPORTS = 'imports'
TYPES = 'types'
PLUGINS = 'plugins'
INTERFACES = 'interfaces'
WORKFLOWS = 'workflows'
POLICIES = 'policies'
RELATIONSHIPS = 'relationships'
PROPERTIES = 'properties'

HOST_TYPE = 'cloudify.types.host'
CONTAINED_IN_REL_TYPE = 'cloudify.relationships.contained_in'
PLUGIN_INSTALLER_PLUGIN = 'cloudify.plugins.plugin_installer'

__author__ = 'ran'

import os
import yaml
import copy
import contextlib
from schemas import DSL_SCHEMA, IMPORTS_SCHEMA
from jsonschema import validate, ValidationError
from yaml.parser import ParserError
from urllib import pathname2url
from urllib2 import urlopen, URLError


def parse_from_path(dsl_file_path, alias_mapping_dict=None, alias_mapping_url=None, resources_url=None):
    with open(dsl_file_path, 'r') as f:
        dsl_string = f.read()
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url, resources_url, dsl_file_path)


def parse_from_url(dsl_url, alias_mapping_dict=None, alias_mapping_url=None, resources_url=None):
    with contextlib.closing(urlopen(dsl_url)) as f:
        dsl_string = f.read()
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url, resources_url, dsl_url)


def parse(dsl_string, alias_mapping_dict=None, alias_mapping_url=None, resources_url=None):
    return _parse(dsl_string, alias_mapping_dict, alias_mapping_url, resources_url)


def _get_alias_mapping(alias_mapping_dict, alias_mapping_url):
    alias_mapping = {}
    if alias_mapping_url is not None:
        with contextlib.closing(urlopen(alias_mapping_url)) as f:
            alias_mapping_string = f.read()
        alias_mapping = dict(alias_mapping.items() + yaml.safe_load(alias_mapping_string).items())
    if alias_mapping_dict is not None:
        alias_mapping = dict(alias_mapping.items() + alias_mapping_dict.items())
    return alias_mapping


def _parse(dsl_string, alias_mapping_dict, alias_mapping_url, resources_url, dsl_location=None):
    alias_mapping = _get_alias_mapping(alias_mapping_dict, alias_mapping_url)
    try:
        parsed_dsl = yaml.safe_load(dsl_string)
    except ParserError, ex:
        raise DSLParsingFormatException(-1, 'Failed to parse DSL: Illegal yaml')
    if parsed_dsl is None:
        raise DSLParsingFormatException(0, 'Failed to parse DSL: Empty yaml')

    combined_parsed_dsl = _combine_imports(parsed_dsl, alias_mapping, dsl_location, resources_url)

    _validate_dsl_schema(combined_parsed_dsl)

    blueprint = combined_parsed_dsl[BLUEPRINT]
    app_name = blueprint['name']

    nodes = blueprint['topology']
    _validate_no_duplicate_nodes(nodes)
    _validate_no_duplicate_interfaces(combined_parsed_dsl)

    top_level_relationships = _process_relationships(combined_parsed_dsl, alias_mapping)

    top_level_policies_and_rules_tuple = _process_policies(combined_parsed_dsl[POLICIES], alias_mapping) if \
        POLICIES in combined_parsed_dsl else ({}, {})

    node_names_set = {node['name'] for node in nodes}
    processed_nodes = map(lambda node: _process_node(node, combined_parsed_dsl, top_level_policies_and_rules_tuple,
                                                     top_level_relationships, node_names_set, alias_mapping), nodes)
    _post_process_nodes(processed_nodes, _get_dict_prop(combined_parsed_dsl, TYPES),
                        _get_dict_prop(combined_parsed_dsl, RELATIONSHIPS))

    top_level_workflows = _process_workflows(combined_parsed_dsl[WORKFLOWS], alias_mapping) if WORKFLOWS in \
                                                                                               combined_parsed_dsl else {}

    response_policies_section = _create_response_policies_section(processed_nodes)

    plan = {
        'name': app_name,
        'nodes': processed_nodes,
        RELATIONSHIPS: top_level_relationships,
        WORKFLOWS: top_level_workflows,
        POLICIES: response_policies_section,
        'policies_events': top_level_policies_and_rules_tuple[0],
        'rules': top_level_policies_and_rules_tuple[1]
    }

    return plan


def _post_process_nodes(processed_nodes, types, relationships):
    node_name_to_node = {node['id']: node for node in processed_nodes}
    host_types = _build_family_descendants_set(types, HOST_TYPE)
    contained_in_rel_types = _build_family_descendants_set(relationships, CONTAINED_IN_REL_TYPE)

    for node in processed_nodes:
        host_id = _extract_node_host_id(node, node_name_to_node, host_types, contained_in_rel_types)
        if host_id:
            node['host_id'] = host_id

    for node in processed_nodes:
        if node['type'] in host_types:
            plugins_to_install = {}
            for another_node in processed_nodes:
                #going over all other nodes, to accumulate plugins from different nodes whose host is the current node
                if another_node['host_id'] == node['id'] and PLUGINS in another_node:
                    #ok to override here since we assume it is the same plugin
                    for plugin_name, plugin_obj in another_node[PLUGINS].iteritems():
                        #only wish to add agent plugins, and only if they're not the installer plugin
                        if plugin_obj['agent_plugin'] == 'true' and plugin_obj['name'] != PLUGIN_INSTALLER_PLUGIN:
                            plugins_to_install[plugin_name] = plugin_obj
            node['plugins_to_install'] = plugins_to_install

    _validate_agent_plugins_on_host_nodes(processed_nodes)


def _validate_agent_plugins_on_host_nodes(processed_nodes):
    for node in processed_nodes:
        if 'host_id' not in node and PLUGINS in node:
            for plugin in node[PLUGINS].itervalues():
                if plugin['agent_plugin'] == 'true':
                    raise DSLParsingLogicException(24, "node {0} has no relationship which makes it contained within "
                                                       "a host and it has an agent plugin named {1}, agent plugins "
                                                       "must be installed on a host".format(node['id'],
                                                                                            plugin['name']))


def _build_family_descendants_set(types_dict, derived_from):
    return {type_name for type_name in types_dict.iterkeys() if _is_derived_from(type_name, types_dict, derived_from)}


def _is_derived_from(type_name, types, derived_from):
    if type_name == derived_from:
        return True
    elif 'derived_from' in types[type_name]:
        return _is_derived_from(types[type_name]['derived_from'], types, derived_from)
    return False


#This method is applicable to both types and relationships. it's concerned with extracting the super types
#recursively, where the merging_func parameter is used to merge them with the current type
def _extract_complete_type_recursive(type_obj, type_name, dsl_container, merging_func, visited_type_names,
                                     is_relationships):
    if type_name in visited_type_names:
        visited_type_names.append(type_name)
        ex = DSLParsingLogicException(100, 'Failed parsing {0} {1}, Circular dependency detected: {2}'.format(
            'relationship' if is_relationships else 'type', type_name, ' --> '.join(visited_type_names)))
        ex.circular_dependency = visited_type_names
        raise ex
    visited_type_names.append(type_name)
    current_level_type = copy.deepcopy(type_obj)
    #halt condition
    if 'derived_from' not in current_level_type:
        return current_level_type

    super_type_name = current_level_type['derived_from']
    if super_type_name not in dsl_container:
        raise DSLParsingLogicException(14,
                                       'Missing definition for {0} {1} which is declared as derived by {0} {2}'
                                       .format('relationship' if is_relationships else 'type', super_type_name,
                                               type_name))

    super_type = dsl_container[super_type_name]
    complete_super_type = _extract_complete_type_recursive(super_type, super_type_name, dsl_container, merging_func,
                                                           visited_type_names, is_relationships)
    return merging_func(complete_super_type, current_level_type)


def _process_relationships(combined_parsed_dsl, alias_mapping):
    processed_relationships = {}
    if RELATIONSHIPS not in combined_parsed_dsl:
        return processed_relationships

    relationships = combined_parsed_dsl[RELATIONSHIPS]

    def rel_inheritance_merging_func(complete_super_type, current_level_type):
        #derive fields
        merged_type = dict(complete_super_type.items() + current_level_type.items())
        return merged_type

    for rel_name, rel_obj in relationships.iteritems():
        complete_rel_obj = _extract_complete_type_recursive(rel_obj, rel_name, relationships,
                                                            rel_inheritance_merging_func, [], True)

        plugins = _get_dict_prop(combined_parsed_dsl, PLUGINS)
        _validate_relationship_fields(complete_rel_obj, plugins, rel_name)
        processed_relationships[rel_name] = copy.deepcopy(complete_rel_obj)
        processed_relationships[rel_name]['name'] = rel_name
        if 'derived_from' in processed_relationships[rel_name]:
            del (processed_relationships[rel_name]['derived_from'])

        if 'workflow' in processed_relationships[rel_name]:
            processed_relationships[rel_name]['workflow'] = _process_ref_or_inline_value(processed_relationships[
                                                                                             rel_name]['workflow'],
                                                                                         'radial', alias_mapping)
    return processed_relationships


def _validate_relationship_fields(rel_obj, plugins, rel_name):
    if 'plugin' in rel_obj and rel_obj['plugin'] not in plugins:
        raise DSLParsingLogicException(19, 'Missing definition for plugin {0}, which is declared for relationship'
                                           ' {1}'.format(rel_obj['plugin'], rel_name))
    if 'bind_at' in rel_obj and rel_obj['bind_at'] not in ('pre_started', 'post_started'):
        raise DSLParsingLogicException(20, 'Relationship {0} has an illegal "bind_at" value {1}; value must '
                                           'be either {2} or {3}'.format(rel_name, rel_obj['bind_at'],
                                       'pre_started', 'post_started'))
    if 'run_on_node' in rel_obj and rel_obj['run_on_node'] not in ('source', 'target'):
        raise DSLParsingLogicException(21, 'Relationship {0} has an illegal "run_on_node" value {1}; value must '
                                           'be either {2} or {3}'.format(rel_name, rel_obj['run_on_node'],
                                       'source', 'target'))


def _create_response_policies_section(processed_nodes):
    response_policies_section = {}
    for processed_node in processed_nodes:
        if POLICIES in processed_node:
            response_policies_section[processed_node['id']] = copy.deepcopy(processed_node[POLICIES])
    return response_policies_section


def _process_policies(policies, alias_mapping):
    processed_policies_events = {}
    processed_rules = {}

    if 'types' in policies:
        for name, policy_event_obj in policies['types'].iteritems():
            processed_policies_events[name] = {}
            processed_policies_events[name]['message'] = policy_event_obj['message']
            processed_policies_events[name]['policy'] = _process_ref_or_inline_value(policy_event_obj, 'policy',
                                                                                     alias_mapping)
    if 'rules' in policies:
        for name, rule_obj in policies['rules'].iteritems():
            processed_rules[name] = copy.deepcopy(rule_obj)

    return processed_policies_events, processed_rules


def _process_workflows(workflows, alias_mapping):
    processed_workflows = {}

    for name, flow_obj in workflows.iteritems():
        processed_workflows[name] = _process_ref_or_inline_value(flow_obj, 'radial', alias_mapping)

    return processed_workflows


def _process_ref_or_inline_value(ref_or_inline_obj, inline_key_name, alias_mapping):
    if 'ref' in ref_or_inline_obj:
        filename = ref_or_inline_obj['ref']
        return _apply_ref(filename, alias_mapping)
    else: #inline
        return ref_or_inline_obj[inline_key_name]


def _validate_no_duplicate_nodes(nodes):
    duplicate = _validate_no_duplicate_element(nodes, lambda node: node['name'])
    if duplicate is not None:
        ex = DSLParsingLogicException(101, 'Duplicate node definition detected, there are {0} nodes with name {'
                                           '1} defined'.format(duplicate[1], duplicate[0]))
        ex.duplicate_node_name = duplicate[0]
        raise ex


def _validate_no_duplicate_interfaces(parsed_dsl):
    def _add_interface_name_or_throw(rel_obj, unique_interfaces):
        if 'interface' in rel_obj:
            if rel_obj['interface']['name'] in unique_interfaces:
                raise DSLParsingLogicException(22, 'Illegal duplicate - interface {0} is defined more than once'
                .format(rel_obj['interface']['name']))
            unique_interfaces.add(rel_obj['interface']['name'])

    top_level_interfaces = _get_dict_prop(parsed_dsl, INTERFACES)
    top_level_relationships = _get_dict_prop(parsed_dsl, RELATIONSHIPS)
    nodes = parsed_dsl[BLUEPRINT]['topology']

    unique_interfaces = set()
    #adding interfaces names from the top-level interfaces definitions -
    #no need to check for duplicates here because of the yaml inherent structure
    unique_interfaces.update(top_level_interfaces.keys())
    #unique_interfaces.update((name for name in top_level_interfaces.keys()))

    #adding interfaces names from the top level relationships definitions
    for rel_obj in top_level_relationships.itervalues():
        _add_interface_name_or_throw(rel_obj, unique_interfaces)

    #adding interfaces names from the instance relationships definitions
    for node in nodes:
        if RELATIONSHIPS in node:
            for rel_obj in node[RELATIONSHIPS]:
                _add_interface_name_or_throw(rel_obj, unique_interfaces)


def _validate_no_duplicate_element(elements, keyfunc):
    elements.sort(key=keyfunc)
    groups = []
    from itertools import groupby

    for key, group in groupby(elements, key=keyfunc):
        groups.append(list(group))
    for group in groups:
        if len(group) > 1:
            return keyfunc(group[0]), len(group)


def _process_node_relationships(alias_mapping, app_name, node, node_name, node_names_set, plugins, processed_node,
                                top_level_relationships):
    if RELATIONSHIPS in node:
        relationships = []
        for relationship in node[RELATIONSHIPS]:
            relationship_type = relationship['type']
            #validating only the instance relationship values - the inherited relationship values if any
            #should have been validated when the top level relationships were processed.
            _validate_relationship_fields(relationship, plugins, relationship_type)
            #validate target field (done separately since it's only available in instance relationships)
            if relationship['target'] not in node_names_set:
                raise DSLParsingLogicException(25, 'a relationship instance under node {0} of type {1} declares an '
                                                   'undefined target node {2}'.format(node_name, relationship_type,
                                                                                      relationship['target']))
            if relationship['target'] == node_name:
                raise DSLParsingLogicException(23, 'a relationship instance under node {0} of type {1} '
                                                   'illegally declares the source node as the target node'.format(
                    node_name, relationship_type))
                #merge relationship instance with relationship type
            if relationship_type not in top_level_relationships:
                raise DSLParsingLogicException(26, 'a relationship instance under node {0} declares an undefined '
                                                   'relationship type {1}'.format(node_name, relationship_type))
            complete_relationship = dict(top_level_relationships[relationship_type].items() + relationship.items())
            #since we've merged with the already-processed top_level_relationships, there are a few changes that need
            #to take place - 'name' is replaced with a [fully qualified] 'target' field, and 'workflow' needs to be
            #re-processed if it is defined in 'relationship', since it overrides any possible already-processed
            #workflows that might have been inherited, and has not yet been processed
            del (complete_relationship['name'])
            complete_relationship['target'] = '{0}.{1}'.format(app_name, complete_relationship['target'])
            if 'workflow' in relationship and relationship['workflow']:
                complete_relationship['workflow'] = _process_ref_or_inline_value(relationship['workflow'], 'radial',
                                                                                 alias_mapping)
            elif 'workflow' not in complete_relationship or not complete_relationship['workflow']:
                complete_relationship['workflow'] = 'define stub_workflow\n\t'
            complete_relationship['state'] = 'reachable'
            relationships.append(complete_relationship)

        processed_node[RELATIONSHIPS] = relationships


def _process_node(node, parsed_dsl, top_level_policies_and_rules_tuple, top_level_relationships, node_names_set,
                  alias_mapping):
    node_type_name = node['type']
    node_name = node['name']
    app_name = parsed_dsl[BLUEPRINT]['name']
    processed_node = {'id': '{0}.{1}'.format(app_name, node_name),
                      'type': node_type_name}

    #handle types
    if TYPES not in parsed_dsl or node_type_name not in parsed_dsl[TYPES]:
        err_message = 'Could not locate node type: {0}; existing types: {1}'.format(node_type_name,
                                                                                    parsed_dsl[TYPES].keys() if
                                                                                    TYPES in parsed_dsl else 'None')
        raise DSLParsingLogicException(7, err_message)

    node_type = parsed_dsl[TYPES][node_type_name]
    complete_node_type = _extract_complete_type(node_type, node_type_name, parsed_dsl)

    #handle plugins and operations
    plugins = {}
    operations = {}
    if INTERFACES in complete_node_type:
        if complete_node_type[INTERFACES] and PLUGINS not in parsed_dsl:
            raise DSLParsingLogicException(5, 'Must provide plugins section when providing interfaces section')

        implementation_interfaces = complete_node_type[INTERFACES]
        _validate_no_duplicate_interfaces_for_node(implementation_interfaces, node_name)
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
            plugins[plugin_name] = _process_plugin(plugin, plugin_name)

            #put operations into node
            if interface_name not in parsed_dsl[INTERFACES]:
                raise DSLParsingLogicException(9, 'Missing interface {0} definition'.format(interface_name))
            interface = parsed_dsl[INTERFACES][interface_name]
            for operation in interface['operations']:
                if operation in operations:
                    #Indicate this implicit operation name needs to be removed as we can only
                    #support explicit implementation in this case
                    operations[operation] = None
                else:
                    operations[operation] = plugin_name
                operations['{0}.{1}'.format(interface_name, operation)] = plugin_name

        operations = dict((operation, plugin) for operation, plugin in operations.iteritems() if plugin is not None)
        processed_node[PLUGINS] = plugins
        processed_node['operations'] = operations

    #handle relationships
    _process_node_relationships(alias_mapping, app_name, node, node_name, node_names_set, plugins, processed_node,
                                top_level_relationships)

    #merge properties
    processed_node[PROPERTIES] = _merge_sub_dicts(complete_node_type, node, PROPERTIES)
    processed_node[PROPERTIES]['cloudify_runtime'] = {}

    #merge workflows
    merged_workflows = _merge_sub_dicts(complete_node_type, node, WORKFLOWS)
    processed_node[WORKFLOWS] = _process_workflows(merged_workflows, alias_mapping)

    #merge policies
    processed_node[POLICIES] = _merge_sub_list(complete_node_type, node, POLICIES)
    _validate_node_policies(processed_node[POLICIES], node_name, top_level_policies_and_rules_tuple)

    return processed_node



def _extract_node_host_id(processed_node, node_name_to_node, host_types, contained_in_rel_types):
    if processed_node['type'] in host_types:
        return processed_node['id']
    else:
        if RELATIONSHIPS in processed_node:
            for rel in processed_node[RELATIONSHIPS]:
                if rel['type'] in contained_in_rel_types:
                    return _extract_node_host_id(node_name_to_node[rel['target']], node_name_to_node, host_types,
                                                 contained_in_rel_types)


def _process_plugin(plugin, plugin_name):
    #'cloudify.plugins.plugin'
    if plugin['derived_from'] not in ('cloudify.plugins.agent_plugin', 'cloudify.plugins.remote_plugin'):
        #TODO: consider changing the below exception to type DSLParsingFormatException..?
        raise DSLParsingLogicException(18, 'plugin {0} has an illegal "derived_from" value {1}; value must be'
                                           ' either {2} or {3}', plugin_name, plugin['derived_from'],
                                       'cloudify.plugins.agent_plugin', 'cloudify.plugins.remote_plugin')
    processed_plugin = copy.deepcopy(plugin[PROPERTIES])
    processed_plugin['name'] = plugin_name
    processed_plugin['agent_plugin'] = str(plugin['derived_from'] == 'cloudify.plugins.agent_plugin').lower()
    return processed_plugin


def _validate_node_policies(policies, node_name, top_level_policies_and_rules_tuple):
    #validating all policies and rules declared are indeed defined in the top level policies section
    for policy_obj in policies:
        policy_name = policy_obj['name']
        if policy_name not in top_level_policies_and_rules_tuple[0]:
            raise DSLParsingLogicException(16, 'Failed to parse node {0}: policy {1} not defined'.format(node_name,
                                                                                                         policy_name))
        for rule in policy_obj['rules']:
            if rule['type'] not in top_level_policies_and_rules_tuple[1]:
                raise DSLParsingLogicException(17, 'Failed to parse node {0}: rule {1} under policy {2} not '
                                                   'defined'.format(node_name, rule['type'], policy_name))


def _merge_sub_list(overridden_dict, overriding_dict, sub_list_key):
    def _get_named_list_dict(sub_list):
        return {entry['name']: entry for entry in sub_list}.items()

    overridden_sub_list = _get_list_prop(overridden_dict, sub_list_key)
    overriding_sub_list = _get_list_prop(overriding_dict, sub_list_key)
    name_to_list_entry = dict(_get_named_list_dict(overridden_sub_list) + _get_named_list_dict(overriding_sub_list))
    return name_to_list_entry.values()


def _merge_sub_dicts(overridden_dict, overriding_dict, sub_dict_key):
    overridden_sub_dict = _get_dict_prop(overridden_dict, sub_dict_key)
    overriding_sub_dict = _get_dict_prop(overriding_dict, sub_dict_key)
    return dict(overridden_sub_dict.items() + overriding_sub_dict.items())


def _validate_no_duplicate_interfaces_for_node(implementation_interfaces, node_name):
    duplicate = _validate_no_duplicate_element(implementation_interfaces, lambda interface: _get_interface_name(
        interface))
    if duplicate is not None:
        ex = DSLParsingLogicException(102, 'Duplicate interface definition detected on node {0}, '
                                           'interface {1} has duplicate definition'.format(node_name, duplicate[0]))
        ex.duplicate_interface_name = duplicate[0]
        ex.node_name = node_name
        raise ex


def _extract_complete_type(dsl_type, dsl_type_name, parsed_dsl):
    def types_inheritance_merging_func(complete_super_type, current_level_type):
        merged_type = current_level_type
        #derive properties
        merged_type[PROPERTIES] = _merge_sub_dicts(complete_super_type, merged_type, PROPERTIES)
        #derive workflows
        merged_type[WORKFLOWS] = _merge_sub_dicts(complete_super_type, merged_type, WORKFLOWS)
        #derive policies
        merged_type[POLICIES] = _merge_sub_list(complete_super_type, merged_type, POLICIES)
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

    return _extract_complete_type_recursive(dsl_type, dsl_type_name, parsed_dsl[TYPES], types_inheritance_merging_func,
        [], False)


def _apply_ref(filename, alias_mapping):
    filename = _apply_alias_mapping_if_available(filename, alias_mapping)
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
                        PROPERTIES in plugin_data and plugin_data[PROPERTIES]['interface'] == interface_name]

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


def _combine_imports(parsed_dsl, alias_mapping, dsl_location, resources_url):
    def _merge_into_dict_or_throw_on_duplicate(from_dict, to_dict, top_level_key, path):
        for key, value in from_dict.iteritems():
            if key not in to_dict:
                to_dict[key] = value
            else:
                path.append(key)
                raise DSLParsingLogicException(4, 'Failed on import: Could not merge {0} due to conflict '
                                                  'on path {1}'.format(top_level_key, ' --> '.join(path)))

    merge_no_override = {INTERFACES, PLUGINS, WORKFLOWS, RELATIONSHIPS}
    merge_one_nested_level_no_override = {POLICIES}

    combined_parsed_dsl = copy.deepcopy(parsed_dsl)
    if IMPORTS not in parsed_dsl:
        return combined_parsed_dsl

    _validate_imports_section(parsed_dsl[IMPORTS], dsl_location)

    ordered_imports_list = []
    _build_ordered_imports_list(parsed_dsl, ordered_imports_list, alias_mapping, dsl_location, resources_url)
    if dsl_location:
        ordered_imports_list = ordered_imports_list[1:]

    for single_import in ordered_imports_list:
        try:
            #(note that this check is only to verify nothing went wrong in the meanwhile, as we've already read
            # from all imported files earlier)
            with contextlib.closing(urlopen(single_import)) as f:
                parsed_imported_dsl = yaml.safe_load(f)
        except URLError, ex:
            error = DSLParsingLogicException(13, 'Failed on import - Unable to open import url {0}; {1}'.format(
                single_import, ex.message))
            error.failed_import = single_import
            raise error

        #combine the current file with the combined parsed dsl we have thus far
        for key, value in parsed_imported_dsl.iteritems():
            if key == IMPORTS: #no need to merge those..
                continue
            if key not in combined_parsed_dsl:
                #simply add this first level property to the dsl
                combined_parsed_dsl[key] = value
            else:
                if key in merge_no_override:
                    #this section will combine dictionary entries of the top level only, with no overrides
                    _merge_into_dict_or_throw_on_duplicate(value, combined_parsed_dsl[key], key, [])
                elif key in merge_one_nested_level_no_override:
                    #this section will combine dictionary entries on up to one nested level, yet without overrides
                    for nested_key, nested_value in value.iteritems():
                        if nested_key not in combined_parsed_dsl[key]:
                            combined_parsed_dsl[key][nested_key] = nested_value
                        else:
                            _merge_into_dict_or_throw_on_duplicate(nested_value, combined_parsed_dsl[key][nested_key],
                                                                   key, [nested_key])
                else:
                    #first level property is not white-listed for merge - throw an exception
                    raise DSLParsingLogicException(3, 'Failed on import: non-mergeable field {0}'.format(key))

    #clean the now unnecessary 'imports' section from the combined dsl
    if IMPORTS in combined_parsed_dsl:
        del combined_parsed_dsl[IMPORTS]
    return combined_parsed_dsl


def _get_import_location_candidate(import_str, resources_url, current_import_context=None):
    #Already url format
    if import_str.startswith('http:') or import_str.startswith('ftp:') or import_str.startswith('file:'):
        return import_str

    #Points to an existing file
    if os.path.exists(import_str):
        return 'file:{0}'.format(pathname2url(import_str))

    if current_import_context:
        candidate_url = current_import_context[:current_import_context.rfind('/') + 1] + import_str
        if _validate_url_exists(candidate_url):
            return candidate_url

    if resources_url:
        return resources_url + import_str


def _validate_url_exists(url):
    try:
        with contextlib.closing(urlopen(url)):
            return True
    except URLError:
        return False


def _build_ordered_imports_list(parsed_dsl, ordered_imports_list, alias_mapping, current_import, resources_url):
    def _build_ordered_imports_list_recursive(parsed_dsl, current_import):
        if current_import is not None:
            ordered_imports_list.append(current_import)

        if IMPORTS not in parsed_dsl:
            return

        for another_import in parsed_dsl[IMPORTS]:
            another_import = _apply_alias_mapping_if_available(another_import, alias_mapping)
            import_url = _get_import_location_candidate(another_import, resources_url, current_import)
            if import_url is None:
                ex = DSLParsingLogicException(13, 'Failed on import - no suitable location found for import {0}'.
                format(another_import))
                ex.failed_import = another_import
                raise ex
            if import_url not in ordered_imports_list:
                try:
                    with contextlib.closing(urlopen(import_url)) as f:
                        imported_dsl = yaml.safe_load(f)
                    _build_ordered_imports_list_recursive(imported_dsl, import_url)
                except URLError, ex:
                    ex = DSLParsingLogicException(13, 'Failed on import - Unable to open import url {0}; {1}'.
                    format(import_url, ex.message))
                    ex.failed_import = import_url
                    raise ex

    current_import = _apply_alias_mapping_if_available(current_import, alias_mapping)
    if current_import is not None:
        current_import = _get_import_location_candidate(current_import, resources_url)
        if current_import is None:
            ex = DSLParsingLogicException(13, 'Failed on import - no suitable location found for import {0}'.
            format(current_import))
            ex.failed_import = current_import
            raise ex
    _build_ordered_imports_list_recursive(parsed_dsl, current_import)


def _validate_dsl_schema(parsed_dsl):
    try:
        validate(parsed_dsl, DSL_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(1, '{0}; Path to error: {1}'.format(ex.message, '.'.join((str(x) for x in ex
        .path))))


def _validate_imports_section(imports_section, dsl_location):
    #imports section is validated separately from the main schema since it is validated for each file separately,
    #while the standard validation runs only after combining all imports together
    try:
        validate(imports_section, IMPORTS_SCHEMA)
    except ValidationError, ex:
        raise DSLParsingFormatException(2, 'Improper "imports" section in yaml {0}; {1}; Path to error: {2}'.format(
            dsl_location, ex.message, '.'.join((str(x) for x in ex.path))))


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