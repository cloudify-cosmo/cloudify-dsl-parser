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

from aria.parser import constants
from aria.parser.exceptions import DSLParsingLogicException
from aria.parser.framework.elements.imports import ImportsLoader
from aria.parser.extension_tools import VersionNumber, ElementExtension


def extend_cloudify_version_1_3():
    return dict(element_extensions=[cloudify_imports_loader_extension])


class CloudifyImportsLoader(ImportsLoader):
    MERGEABLE_FROM_DSL = [
        constants.INPUTS,
        constants.OUTPUTS,
        constants.NODE_TEMPLATES,
    ]

    def merge_parsed_into_combined(self, **kwargs):
        kwargs['merge_no_override'] = self.MERGE_NO_OVERRIDE.copy()
        version = kwargs['version']
        if version['definitions_version'].number > VersionNumber(1, 2):
            kwargs['merge_no_override'].update(self.MERGEABLE_FROM_DSL)
        super(CloudifyImportsLoader, self).merge_parsed_into_combined(**kwargs)

    def assert_mergeable(self, key_holder):
        if key_holder.value in self.MERGEABLE_FROM_DSL:
            raise DSLParsingLogicException(
                3,
                "Import failed: non-mergeable field: '{0}'. "
                "{0} can be imported multiple times only from "
                "cloudify_dsl_1_3 and above.".format(key_holder.value))
        super(CloudifyImportsLoader, self).assert_mergeable(key_holder)

cloudify_imports_loader_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=ImportsLoader,
    new_element=CloudifyImportsLoader)
