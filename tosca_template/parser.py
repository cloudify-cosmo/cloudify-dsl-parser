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

from collections import defaultdict

import requests

from .framework import validate_version_schema, handle_imports, parse_blueprint
from .import_resolver import DefaultImportResolver
from .functions import validate_functions


def parse(uri,
          resources_base_url=None,
          resolver=None,
          validate_version=True):
    scheme, _ = uri.split('://', 1)
    return _PARSE_HANDLERS_PER_URI_SCHEMES[scheme](
        uri, resources_base_url, resolver, validate_version)


def parse_from_path(dsl_file_path,
                    resources_base_url=None,
                    resolver=None,
                    validate_version=True):
    with open(dsl_file_path, 'r') as f:
        return parse_from_string(
            f.read(),
            resources_base_url=resources_base_url,
            dsl_location=dsl_file_path,
            resolver=resolver,
            validate_version=validate_version)


def parse_from_url(
        dsl_url,
        resources_base_url=None,
        resolver=None,
        validate_version=True):
    response = requests.get(dsl_url, stream=True)
    if response.status_code != 200:
        raise Exception  # todo: sort exception
    return parse_from_string(
        response.raw.read(),
        resources_base_url=resources_base_url,
        dsl_location=dsl_url,
        resolver=resolver,
        validate_version=validate_version)


def parse_from_string(
        dsl_string,
        resources_base_url,
        dsl_location=None,
        resolver=None,
        validate_version=True):
    resolver = resolver or DefaultImportResolver()

    parsed_dsl_holder = load_yaml(
        raw_yaml=dsl_string,
        error_message='Failed to parse DSL',
        filename=dsl_location)

    version = validate_version_schema(
        parsed_dsl_holder,
        validate_version)
    resource_base, merged_blueprint_holder = handle_imports(
        parsed_dsl_holder,
        resources_base_url,
        version,
        resolver,
        validate_version)
    plan = parse_blueprint(
        merged_blueprint_holder,
        resource_base,
        validate_version)

    validate_functions(plan)
    return plan

_PARSE_HANDLERS_PER_URI_SCHEMES = defaultdict(
    default_factory=lambda: parse_from_path,
    http=parse_from_url,
    https=parse_from_url,
)
