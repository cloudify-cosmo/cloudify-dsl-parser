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

from collections import namedtuple

from .exceptions import DSLParsingLogicException


VERSION = 'tosca_definitions_version'
DSL_VERSION_PREFIX = 'cloudify_dsl_{0}'
DSL_VERSION_1_0 = DSL_VERSION_PREFIX.format('1_0')
DSL_VERSION_1_1 = DSL_VERSION_PREFIX.format('1_1')
DSL_VERSION_1_2 = DSL_VERSION_PREFIX.format('1_2')
DSL_VERSION_1_3 = DSL_VERSION_PREFIX.format('1_3')
SUPPORTED_VERSIONS = (
    DSL_VERSION_1_0,
    DSL_VERSION_1_1,
    DSL_VERSION_1_2,
    DSL_VERSION_1_3,
)
VersionDetails = namedtuple('VersionDetails', 'major, minor, micro')


def validate_dsl_version(dsl_version):
    if dsl_version not in SUPPORTED_VERSIONS:
        raise DSLParsingLogicException(
            29,
            'Unexpected tosca_definitions_version {0}; Currently '
            'supported versions are: {1}'
            .format(dsl_version, SUPPORTED_VERSIONS))


def parse_dsl_version(dsl_version):
    if not dsl_version:
        raise DSLParsingLogicException(
            71,
            '{0} is missing or empty'.format(VERSION))

    if not isinstance(dsl_version, basestring):
        raise DSLParsingLogicException(
            72,
            'Invalid {0}: {1} is not a string'.format(VERSION, dsl_version))

    if not dsl_version.startswith(DSL_VERSION_PREFIX.format('')):
        raise DSLParsingLogicException(
            73, "Invalid {0}: '{1}', "
                "expected a value following this format: '{2}'"
                .format(VERSION, dsl_version, DSL_VERSION_1_0))

    short_dsl_version = dsl_version.replace(
        DSL_VERSION_PREFIX.format(''), '', 1)
    if '_' not in short_dsl_version:
        raise DSLParsingLogicException(
            73, "Invalid {0}: '{1}', "
                "expected a value following this format: '{2}'"
                .format(VERSION, dsl_version, DSL_VERSION_1_0))

    version_parts = short_dsl_version.split('_')
    major, minor = version_parts[0], version_parts[1]
    micro = version_parts[2] if len(version_parts) > 2 else None

    if not major.isdigit():
        raise DSLParsingLogicException(
            74,
            "Invalid {0}: '{1}', "
            "major version is '{2}' while expected to be a number"
            .format(VERSION, dsl_version, major))

    if not minor.isdigit():
        raise DSLParsingLogicException(
            75,
            "Invalid {0}: '{1}', "
            "minor version is '{2}' while expected to be a number"
            .format(VERSION, dsl_version, minor))

    if micro and not micro.isdigit():
        raise DSLParsingLogicException(
            76,
            "Invalid {0}: '{1}', "
            "micro version is '{2}' while expected to be a number"
            .format(VERSION, dsl_version, micro))

    return VersionDetails(
        int(major), int(minor), int(micro) if micro else None)


def process_dsl_version(dsl_version):
    version_definitions_name = DSL_VERSION_PREFIX[:-4]
    version_definitions_version = parse_dsl_version(dsl_version)
    if version_definitions_version.micro is None:
        version_definitions_version = (
            version_definitions_version.major,
            version_definitions_version.minor,
        )
    return {
        'raw': dsl_version,
        'definitions_name': version_definitions_name,
        'definitions_version': version_definitions_version,
    }


def version_description(dsl_version_tuple):
    version = []
    for index in range(2):
        if index < len(dsl_version_tuple):
            version.append(dsl_version_tuple[index])
        else:
            version.append(0)
    return DSL_VERSION_PREFIX.format('{0}_{1}'.format(*version))
