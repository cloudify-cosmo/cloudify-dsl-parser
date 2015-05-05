########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from dsl_parser import (constants,
                        exceptions)
from dsl_parser.elements import (properties,
                                 misc)
from dsl_parser.framework.elements import (DictElement,
                                           Element,
                                           Leaf,
                                           Dict)


class OperationImplementation(Element):

    schema = Leaf(type=str)

    def parse(self):
        return self.initial_value if self.initial_value is not None else ''


class OperationExecutor(Element):

    schema = Leaf(type=str)

    def validate(self):
        if self.initial_value is None:
            return
        value = self.initial_value
        valid_executors = [constants.CENTRAL_DEPLOYMENT_AGENT,
                           constants.HOST_AGENT]
        if value not in valid_executors:
            full_operation_name = '{0}.{1}'.format(
                self.ancestor(Interface).name,
                self.ancestor(Operation).name)
            raise exceptions.DSLParsingLogicException(
                28, 'Operation {0} has an illegal executor value: {1}. '
                    'valid values are [{2}]'
                    .format(full_operation_name,
                            value,
                            ','.join(valid_executors)))


class NodeTemplateOperationInputs(Element):

    schema = Leaf(type=dict)

    def parse(self):
        return self.initial_value if self.initial_value is not None else {}


class OperationMaxRetries(Element):

    schema = Leaf(type=int)
    requires = {
        misc.ToscaDefinitionsVersion: ['version']
    }

    def validate(self, version):
        value = self.initial_value
        if value is None:
            return
        if version < (1, 1):
            raise exceptions.DSLParsingLogicException(
                81,
                'operation max_retries '
                'is only supported in dsl versions greater or equal to'
                'cloudify_dsl_1_1')
        if value < -1:
            raise ValueError('{0} value must be either -1 to specify unlimited'
                             ' retries or a non negative number but got {1}.'
                             .format(self.name, value))


class OperationRetryInterval(Element):

    schema = Leaf(type=(int, float, long))
    requires = {
        misc.ToscaDefinitionsVersion: ['version']
    }

    def validate(self, version):
        value = self.initial_value
        if value is None:
            return
        if version < (1, 1):
            raise exceptions.DSLParsingLogicException(
                81,
                'operation retry_interval '
                'is only supported in dsl versions greater or equal to'
                'cloudify_dsl_1_1')
        if value is not None and value < 0:
            raise ValueError('{0} value must be a non negative number but got'
                             ' {1}.'.format(self.name, value))


class Operation(Element):

    def parse(self):
        if isinstance(self.initial_value, basestring):
            return {
                'implementation': self.initial_value,
                'executor': None,
                'inputs': {},
                'max_retries': None,
                'retry_interval': None
            }
        else:
            return self.build_dict_result()


class NodeTypeOperation(Operation):

    schema = [
        Leaf(type=str),
        {
            'implementation': OperationImplementation,
            'inputs': properties.Schema,
            'executor': OperationExecutor,
            'max_retries': OperationMaxRetries,
            'retry_interval': OperationRetryInterval,
        }
    ]


class NodeTemplateOperation(Operation):

    schema = [
        Leaf(type=str),
        {
            'implementation': OperationImplementation,
            'inputs': NodeTemplateOperationInputs,
            'executor': OperationExecutor,
            'max_retries': OperationMaxRetries,
            'retry_interval': OperationRetryInterval,
        }
    ]


class Interface(DictElement):
    pass


class NodeTemplateInterface(Interface):

    schema = Dict(type=NodeTemplateOperation)


class NodeTemplateInterfaces(DictElement):

    schema = Dict(type=NodeTemplateInterface)


class NodeTypeInterface(Interface):

    schema = Dict(type=NodeTypeOperation)


class NodeTypeInterfaces(DictElement):

    schema = Dict(type=NodeTypeInterface)
