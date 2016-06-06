#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

"""
Aria's parser Package
Path: aria.parser

Methods:
    * default_parser - Parser class instance with default values
    * default_expander - ParserExpander class instance with default values
    * parse - default_parser.parse method
    * expand - default parser language expansion method

"""

from functools import partial

from aria.parser import Parser, extend
from aria.parser.extension_tools import VersionStructure, VersionNumber

from .cloudify_profile_v1_0 import extend_cloudify_version_1_0
from .cloudify_profile_v1_1 import extend_cloudify_version_1_1
from .cloudify_profile_v1_2 import extend_cloudify_version_1_2
from .cloudify_profile_v1_3 import extend_cloudify_version_1_3
from .VERSION import version as __version__

__all__ = [
    'extend',
    'parse',
    'default_parser',
    'cloudify_profile_name',
]

cloudify_profile_name = 'cloudify_dsl'
CloudifyProfile = partial(VersionStructure, profile=cloudify_profile_name)

extend(
    version_structure=CloudifyProfile(number=VersionNumber(1, 0, 0)),
    **extend_cloudify_version_1_0())
extend(
    version_structure=CloudifyProfile(number=VersionNumber(1, 1, 0)),
    **extend_cloudify_version_1_1())
extend(
    version_structure=CloudifyProfile(number=VersionNumber(1, 2, 0)),
    **extend_cloudify_version_1_2())

extend(
    version_structure=CloudifyProfile(number=VersionNumber(1, 3, 0)),
    **extend_cloudify_version_1_3())

default_parser = Parser()
parse = default_parser.parse
