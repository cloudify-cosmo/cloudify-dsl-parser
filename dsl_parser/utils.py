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

import contextlib
import importlib
import urllib2
import sys

import yaml.parser

from dsl_parser import yaml_loader
from dsl_parser import functions
from dsl_parser.constants import RESOLVER_IMPLEMENTATION_KEY, \
    RESLOVER_PARAMETERS_KEY
from dsl_parser.exceptions import (DSLParsingLogicException,
                                   DSLParsingFormatException)
from dsl_parser.import_resolver.default_import_resolver import \
    DefaultImportResolver


class ResolverInstantiationError(Exception):
    pass


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
        schema_properties,
        undefined_property_error_message,
        missing_property_error_message,
        node_name):
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
                "Unexpected type defined in property schema for property '{0}'"
                " - unknown type is '{1}'".format(prop_key, prop_type))

        raise DSLParsingLogicException(
            50, "Property type validation failed: Property '{0}' type "
                "is '{1}', yet it was assigned with the value '{2}'"
                .format(prop_key, prop_type, prop_val))


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


def create_import_resolver(resolver_configuration):
    if resolver_configuration:
        resolver_class_path = resolver_configuration.get(
            RESOLVER_IMPLEMENTATION_KEY)
        parameters = resolver_configuration.get(RESLOVER_PARAMETERS_KEY, {})
        if parameters and not isinstance(parameters, dict):
            raise ResolverInstantiationError(
                'Invalid parameters supplied for the resolver ({0}): '
                'parameters must be a dictionary and not {1}'
                .format(resolver_class_path or 'DefaultImportResolver',
                        type(parameters).__name__))
        try:
            if resolver_class_path:
                # custom import resolver
                return get_class_instance(resolver_class_path, parameters)
            else:
                # default import resolver
                return DefaultImportResolver(**parameters)
        except Exception, ex:
            raise ResolverInstantiationError(
                'Failed to instantiate resolver ({0}). {1}'
                .format(resolver_class_path or 'DefaultImportResolver',
                        str(ex)))
    return DefaultImportResolver()


def get_class_instance(class_path, properties):
    """Returns an instance of a class from a string formatted as module:class
    the given *args, **kwargs are passed to the instance's __init__"""
    if not properties:
        properties = {}
    try:
        cls = get_class(class_path)
        instance = cls(**properties)
    except Exception as e:
        exc_type, exc, traceback = sys.exc_info()
        raise RuntimeError('Failed to instantiate {0}, error: {1}'
                           .format(class_path, e)), None, traceback

    return instance


def get_class(class_path):
    """Returns a class from a string formatted as module:class"""
    if not class_path:
        raise ValueError('class path is missing or empty')

    if not isinstance(class_path, basestring):
        raise ValueError('class path is not a string')

    class_path = class_path.strip()
    if ':' not in class_path or class_path.count(':') > 1:
        raise ValueError('Invalid class path, expected format: '
                         'module:class')

    class_path_parts = class_path.split(':')
    class_module_str = class_path_parts[0].strip()
    class_name = class_path_parts[1].strip()

    if not class_module_str or not class_name:
        raise ValueError('Invalid class path, expected format: '
                         'module:class')

    module = importlib.import_module(class_module_str)
    if not hasattr(module, class_name):
        raise ValueError('module {0}, does not contain class {1}'
                         .format(class_module_str, class_name))

    return getattr(module, class_name)
