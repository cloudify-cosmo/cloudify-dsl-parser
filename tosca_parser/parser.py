# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from functools import partial

from .framework import validate_version_schema, handle_imports, parse_blueprint
from .import_resolver import DefaultImportResolver
from .functions import validate_functions
from .yaml_loader import load
from . import uri_data_reader


class Parser(object):
    def __init__(self, import_resolver=None, validate_version=True):
        """

        :param import_resolver:
        :param validate_version:
        """
        self.import_resolver = import_resolver or DefaultImportResolver()
        self.validate_version = validate_version

    def __getattr__(self, item):
        if not item.startswith('parse_from'):
            return super(Parser, self).__getattribute__(item)
        read_from_method_name = item.replace('parse_', 'read_', 1)
        try:
            read_method = getattr(uri_data_reader, read_from_method_name)
        except AttributeError:
            return super(Parser, self).__getattribute__(item)

        return partial(self._parser_method_template, read_method)

    def parse(self, uri):
        """

        :param uri:
        :return:
        """
        return self._parser_method_template(
            read_method=uri_data_reader.read_data_from_uri,
            uri=uri)

    def _parser_method_template(self, read_method, uri):
        dsl_string = read_method(uri)
        return self.parse_from_string(dsl_string, dsl_location=uri)

    def parse_from_string(self, dsl_string, dsl_location=None):
        parsed_dsl_holder = load(
            raw_yaml=dsl_string,
            error_message='Failed to parse DSL',
            filename=dsl_location)

        version = validate_version_schema(
            parsed_dsl_holder, self.validate_version)

        if dsl_location and not os.path.isdir(dsl_location):
            dsl_location = os.path.dirname(dsl_location)

        resource_base, merged_blueprint_holder = handle_imports(
            parsed_dsl_holder,
            dsl_location,
            version,
            self.import_resolver,
            self.validate_version)

        plan = parse_blueprint(
            merged_blueprint_holder,
            resource_base,
            self.validate_version)

        validate_functions(plan)
        return plan
