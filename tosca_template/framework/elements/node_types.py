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

from ...interfaces import merge_node_type_interfaces
from ... import constants, utils
from .. import Value, Dict
from .types import Type, Types, TypeDerivedFrom, derived_from_predicate
from .operation import NodeTypeInterfaces
from .data_types import SchemaWithInitialDefault, DataTypes


class NodeType(Type):
    schema = {
        'derived_from': TypeDerivedFrom,
        'interfaces': NodeTypeInterfaces,
        'properties': SchemaWithInitialDefault,
    }
    requires = {
        'self': [Value('super_type',
                       predicate=derived_from_predicate,
                       required=False)],
        DataTypes: [Value('data_types')],
    }

    def parse(self, super_type, data_types):
        node_type = self.build_dict_result()
        if not node_type.get('derived_from'):
            node_type.pop('derived_from', None)
        if super_type:
            node_type[constants.PROPERTIES] = utils.merge_schemas(
                overridden_schema=super_type.get('properties', {}),
                overriding_schema=node_type.get('properties', {}),
                data_types=data_types)
            node_type[constants.INTERFACES] = merge_node_type_interfaces(
                overridden_interfaces=super_type[constants.INTERFACES],
                overriding_interfaces=node_type[constants.INTERFACES])
        node_type[constants.TYPE_HIERARCHY] = self.create_type_hierarchy(
            super_type)
        self.fix_properties(node_type)
        return node_type


class NodeTypes(Types):
    schema = Dict(type=NodeType)
    provides = ['host_types']

    def calculate_provided(self):
        return {
            'host_types': self._types_derived_from(constants.HOST_TYPE),
        }

    def _types_derived_from(self, derived_from):
        return set(type_name
                   for type_name, _type in self.value.items()
                   if derived_from in _type[constants.TYPE_HIERARCHY])
