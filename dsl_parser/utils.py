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
import contextlib
import urllib2

import yaml.parser

from dsl_parser import yaml_loader
from dsl_parser import functions
from dsl_parser import exceptions
from dsl_parser.exceptions import (DSLParsingLogicException,
                                   DSLParsingFormatException)


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


def _property_description(path, name=None):
    if not path:
        return name
    if name is not None:
        path = copy.copy(path)
        path.append(name)
    return '.'.join(path)


def merge_schema_and_instance_properties(
        instance_properties,
        schema_properties,
        data_types,
        undefined_property_error_message,
        missing_property_error_message,
        node_name,
        path=None):
    if path is None:
        path = []
    flattened_schema_props = flatten_schema(schema_properties)

    # validate instance properties don't
    # contain properties that are not defined
    # in the schema.

    for key in instance_properties.iterkeys():
        if key not in flattened_schema_props:
            ex = DSLParsingLogicException(
                106,
                undefined_property_error_message.format(
                    node_name,
                    _property_description(path, key)))
            ex.property = key
            raise ex

    merged_properties = dict(flattened_schema_props.items() +
                             instance_properties.items())
    result = {}
    for key, value in merged_properties.iteritems():
        if value is None:
            ex = DSLParsingLogicException(
                107,
                missing_property_error_message.format(
                    node_name,
                    _property_description(path, key)))
            ex.property = key
            raise ex
        prop_path = copy.copy(path)
        prop_path.append(key)
        result[key] = parse_value(
            value=value,
            type_name=schema_properties.get(key).get('type'),
            data_types=data_types,
            undefined_property_error_message=undefined_property_error_message,
            missing_property_error_message=missing_property_error_message,
            node_name=node_name,
            path=prop_path)

    return result


def parse_value(
        value,
        type_name,
        data_types,
        undefined_property_error_message,
        missing_property_error_message,
        node_name,
        path):
    if type_name is None:
        return value
    if functions.parse(value) != value:
        # intrinsic function - not validated at the moment
        return value
    if type_name == 'integer':
        if isinstance(value, (int, long)) and not isinstance(
                value, bool):
            return value
    elif type_name == 'float':
        if isinstance(value, (int, float, long)) and not isinstance(
                value, bool):
            return value
    elif type_name == 'boolean':
        if isinstance(value, bool):
            return value
    elif type_name == 'string':
        return value
    elif type_name in data_types:
        if isinstance(value, dict):
            data_schema = data_types[type_name]['properties']
            undef_msg = undefined_property_error_message
            return merge_schema_and_instance_properties(
                value,
                data_schema,
                data_types=data_types,
                undefined_property_error_message=undef_msg,
                missing_property_error_message=missing_property_error_message,
                node_name=node_name,
                path=path)
    else:
        raise RuntimeError(
            "Unexpected type defined in property schema for property '{0}'"
            " - unknown type is '{1}'".format(
                _property_description(path),
                type_name))

    raise DSLParsingLogicException(
        exceptions.ERROR_VALUE_DOES_NOT_MATCH_TYPE,
        "Property type validation failed in '{0}': property "
        "'{1}' type is '{2}', yet it was assigned with the "
        "value '{3}'".format(
            node_name,
            _property_description(path),
            type_name,
            value))


def load_yaml(raw_yaml, error_message, filename=None):
    try:
        return yaml_loader.load(raw_yaml, filename)
    except yaml.parser.ParserError, ex:
        raise DSLParsingFormatException(-1, '{0}: Illegal yaml; {1}'
                                        .format(error_message, ex))


def url_exists(url):
    try:
        with contextlib.closing(urllib2.urlopen(url)):
            return True
    except urllib2.URLError:
        return False
