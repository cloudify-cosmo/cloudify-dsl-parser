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

from aria.parser.extension_tools import ElementExtension
from aria.parser.framework.elements.policies import Policies
from aria.parser.framework.elements.node_templates import NodeTemplateCapabilities


def extend_cloudify_version_1_3():
    return dict(element_extensions=[
        cloudify_node_template_capabilities_extension,
        cloudify_policies_extension,
    ])


cloudify_node_template_capabilities_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=NodeTemplateCapabilities)


cloudify_policies_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=Policies)
