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

from aria.parser.framework.functions import Concat
from aria.parser.framework.elements.plugins import PluginInstallArguments
from aria.parser.framework.elements.operation import (
    OperationMaxRetries,
    OperationRetryInterval,
)
from aria.parser.extension_tools import (
    ElementExtension,
    IntrinsicFunctionExtension,
)


def extend_cloudify_version_1_1():
    return dict(
        element_extensions=[
            cloudify_operation_max_retries_extension,
            cloudify_operation_retry_interval_extension,
            cloudify_plugin_install_arguments_extension,
        ],
        function_extensions=[cloudify_concat_extension],
    )

cloudify_operation_max_retries_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=OperationMaxRetries)

cloudify_operation_retry_interval_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=OperationRetryInterval)

cloudify_plugin_install_arguments_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginInstallArguments)

cloudify_concat_extension = IntrinsicFunctionExtension(
    action=IntrinsicFunctionExtension.ADD_FUNCTION_ACTION,
    name='concat',
    function=Concat)
