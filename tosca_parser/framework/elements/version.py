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

from ...version import (
    VERSION,
    validate_dsl_version,
    process_dsl_version,
    parse_dsl_version,
)
from ...exceptions import DSLParsingLogicException
from ...models import Version
from . import Element, Leaf


class ToscaDefinitionsVersion(Element):
    schema = Leaf(type=str)
    provides = ['version']

    def validate(self):
        if self.initial_value is None:
            raise DSLParsingLogicException(
                27, '{0} field must appear in the main blueprint file'
                    .format(VERSION))
        validate_dsl_version(self.initial_value)

    def parse(self):
        return Version(process_dsl_version(self.initial_value))

    def calculate_provided(self):
        return {'version': parse_dsl_version(self.initial_value)}
