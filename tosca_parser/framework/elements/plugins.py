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

from ...exceptions import DSLParsingLogicException
from ... import constants
from .version import ToscaDefinitionsVersion
from . import Element, Leaf, Dict, DictElement


class PluginExecutor(Element):
    required = True
    schema = Leaf(type=str)

    def validate(self):
        if self.initial_value not in [constants.CENTRAL_DEPLOYMENT_AGENT,
                                      constants.HOST_AGENT]:
            raise DSLParsingLogicException(
                18,
                "Plugin '{0}' has an illegal "
                "'{1}' value '{2}'; value "
                "must be either '{3}' or '{4}'"
                .format(self.ancestor(Plugin).name,
                        self.name,
                        self.initial_value,
                        constants.CENTRAL_DEPLOYMENT_AGENT,
                        constants.HOST_AGENT))


class PluginSource(Element):
    schema = Leaf(type=str)


class PluginInstall(Element):
    schema = Leaf(type=bool)

    def parse(self):
        return self.initial_value if self.initial_value is not None else True


class PluginVersionValidatedElement(Element):
    schema = Leaf(type=str)
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }
    min_version = None

    def validate(self, version, validate_version):
        if not self.min_version:
            raise RuntimeError('Illegal state, please specify min_version')
        if validate_version:
            self.validate_version(version, self.min_version)


class PluginInstallArguments(PluginVersionValidatedElement):
    min_version = (1, 1)


class PluginPackageName(PluginVersionValidatedElement):
    min_version = (1, 2)


class PluginPackageVersion(PluginVersionValidatedElement):
    min_version = (1, 2)


class PluginSupportedPlatform(PluginVersionValidatedElement):
    min_version = (1, 2)


class PluginDistribution(PluginVersionValidatedElement):
    min_version = (1, 2)


class PluginDistributionVersion(PluginVersionValidatedElement):
    min_version = (1, 2)


class PluginDistributionRelease(PluginVersionValidatedElement):
    min_version = (1, 2)


class Plugin(DictElement):
    schema = {
        'source': PluginSource,
        'executor': PluginExecutor,
        'install': PluginInstall,
        'install_arguments': PluginInstallArguments,
        'package_name': PluginPackageName,
        'package_version': PluginPackageVersion,
        'supported_platform': PluginSupportedPlatform,
        'distribution': PluginDistribution,
        'distribution_version': PluginDistributionVersion,
        'distribution_release': PluginDistributionRelease,
    }

    def validate(self):
        if not self.child(PluginInstall).value:
            return
        if (self.child(PluginSource).value or
                self.child(PluginPackageName).value):
            return
        raise DSLParsingLogicException(
            50,
            "Plugin '{0}' needs to be installed, "
            "but does not declare a source or package_name property"
            .format(self.name))

    def parse(self):
        result = super(Plugin, self).parse()
        result['name'] = self.name
        return result


class Plugins(DictElement):
    schema = Dict(type=Plugin)
