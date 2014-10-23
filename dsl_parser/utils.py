########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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
import copy

from dsl_parser import functions
from dsl_parser.exceptions import DSLParsingLogicException


def merge_sub_dicts(overridden_dict, overriding_dict, sub_dict_key):
    overridden_sub_dict = overridden_dict.get(sub_dict_key, {})
    overriding_sub_dict = overriding_dict.get(sub_dict_key, {})
    return dict(overridden_sub_dict.items() + overriding_sub_dict.items())


def flatten_schema(schema):
    flattened_schema_props = {}
    for prop_key, prop in schema.iteritems():
        if 'default' in prop:
            flattened_schema_props[prop_key] = prop['default']
        else:
            flattened_schema_props[prop_key] = None
    return flattened_schema_props


def merge_schema_and_instance_properties(
        instance_properties,
        impl_properties,
        schema_properties,
        undefined_property_error_message,
        missing_property_error_message,
        node_name):
    instance_properties = dict(instance_properties.items() +
                               impl_properties.items())

    flattened_schema_props = flatten_schema(schema_properties)

    # validate instance properties don't
    # contain properties that are not defined
    # in the schema.

    for key in instance_properties.iterkeys():
        if key not in flattened_schema_props:
            ex = DSLParsingLogicException(
                106,
                undefined_property_error_message.format(node_name, key))
            ex.property = key
            raise ex

    merged_properties = dict(flattened_schema_props.items() +
                             instance_properties.items())

    for key, value in merged_properties.iteritems():
        if value is None:
            ex = DSLParsingLogicException(
                107,
                missing_property_error_message.format(node_name, key))
            ex.property = key
            raise ex

    _validate_properties_types(merged_properties, schema_properties)

    return merged_properties


def _validate_properties_types(properties, properties_schema):
    for prop_key, prop in properties_schema.iteritems():
        prop_type = prop.get('type')
        if prop_type is None:
            continue
        prop_val = properties[prop_key]

        if functions.parse(prop_val) != prop_val:
            # intrinsic function - not validated at the moment
            continue

        if prop_type == 'integer':
            if isinstance(prop_val, (int, long)) and not isinstance(
                    prop_val, bool):
                continue
        elif prop_type == 'float':
            if isinstance(prop_val, (int, float, long)) and not isinstance(
                    prop_val, bool):
                continue
        elif prop_type == 'boolean':
            if isinstance(prop_val, bool):
                continue
        elif prop_type == 'string':
            continue
        else:
            raise RuntimeError(
                'Unexpected type defined in property schema for property {0} -'
                ' unknown type is {1}'.format(prop_key, prop_type))

        raise DSLParsingLogicException(
            50, 'Property type validation failed: Property {0} type '
                'is {1}, yet it was assigned with the value {2}'
                .format(prop_key, prop_type, prop_val))


def extract_complete_type_recursive(dsl_type,
                                    dsl_type_name,
                                    dsl_container,
                                    merging_func,
                                    is_relationships,
                                    visited_type_names=None):

    """
    This method is applicable to both types and relationships.
    it's concerned with extracting the super types recursively,
    where the merging_func parameter is used
    to merge them with the current type

    :param dsl_type:
    :param dsl_type_name:
    :param dsl_container:
    :param merging_func:
    :param is_relationships:
    :param visited_type_names:
    :return:
    """

    if not visited_type_names:
        visited_type_names = []
    if dsl_type_name in visited_type_names:
        visited_type_names.append(dsl_type_name)
        ex = DSLParsingLogicException(
            100, 'Failed parsing {0} {1}, Circular dependency detected: {2}'
                 .format('relationship' if is_relationships else 'type',
                         dsl_type_name,
                         ' --> '.join(visited_type_names)))
        ex.circular_dependency = visited_type_names
        raise ex
    visited_type_names.append(dsl_type_name)
    current_level_type = copy.deepcopy(dsl_type)

    # halt condition
    if 'derived_from' not in current_level_type:
        return current_level_type

    super_type_name = current_level_type['derived_from']
    if super_type_name not in dsl_container:
        raise DSLParsingLogicException(
            14, 'Missing definition for {0} {1} which is declared as derived '
                'by {0} {2}'
                .format('relationship' if is_relationships else 'type',
                        super_type_name,
                        dsl_type_name))

    super_type = dsl_container[super_type_name]
    complete_super_type = extract_complete_type_recursive(
        dsl_type=super_type,
        dsl_type_name=super_type_name,
        dsl_container=dsl_container,
        merging_func=merging_func,
        visited_type_names=visited_type_names,
        is_relationships=is_relationships)
    return merging_func(complete_super_type, current_level_type)
