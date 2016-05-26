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

from aria.parser.framework.elements.misc import DSLDefinitions, Description
from aria.parser.framework.elements.data_types import (
    SchemaPropertyRequired, DataTypes)
from aria.parser.framework.elements.plugins import (
    PluginPackageName,
    PluginPackageVersion,
    PluginSupportedPlatform,
    PluginDistribution,
    PluginDistributionVersion,
    PluginDistributionRelease,
)
from aria.parser.extension_tools import ElementExtension


def extend_cloudify_version_1_2():
    return dict(
        element_extensions=[
            cloudify_schema_property_required_extension,
            cloudify_data_types_extension,
            cloudify_dsl_definitions_extension,
            cloudify_description_extension,
            cloudify_plugin_package_name_extension,
            cloudify_plugin_package_version_extension,
            cloudify_plugin_supported_platform_extension,
            cloudify_plugin_distribution_extension,
            cloudify_plugin_distribution_version_extension,
            cloudify_plugin_distribution_release_extension,
            cloudify_policies_extension,
        ],
    )

cloudify_schema_property_required_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=SchemaPropertyRequired)

cloudify_data_types_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=DataTypes)

cloudify_dsl_definitions_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=DSLDefinitions)

cloudify_description_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=Description)

cloudify_plugin_package_name_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginPackageName)

cloudify_plugin_package_version_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginPackageVersion)

cloudify_plugin_supported_platform_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginSupportedPlatform)

cloudify_plugin_distribution_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginDistribution)

cloudify_plugin_distribution_version_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginDistributionVersion)

cloudify_plugin_distribution_release_extension = ElementExtension(
    action=ElementExtension.CHANGE_ELEMENT_VERSION,
    target_element=PluginDistributionRelease)

