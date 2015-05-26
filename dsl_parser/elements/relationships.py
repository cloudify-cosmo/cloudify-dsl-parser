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
                        utils)
from dsl_parser.interfaces import interfaces_parser
from dsl_parser.elements import (properties,
                                 operation,
                                 plugins as _plugins,
                                 types)
from dsl_parser.framework.requirements import Value, Requirement
from dsl_parser.framework.elements import Dict


class Relationship(types.Type):

    schema = {
        'derived_from': types.RelationshipDerivedFrom,
        'properties': properties.Schema,
        'source_interfaces': operation.NodeTypeInterfaces,
        'target_interfaces': operation.NodeTypeInterfaces,
    }
    requires = {
        'inputs': [Requirement('resource_base', required=False)],
        _plugins.Plugins: [Value('plugins')],
        'self': [Value('super_type',
                       predicate=types.derived_from_predicate,
                       required=False)]
    }

    def parse(self, super_type, plugins, resource_base):
        relationship_type = self.build_dict_result()
        if not relationship_type.get('derived_from'):
            relationship_type.pop('derived_from', None)
        relationship_type_name = self.name

        if super_type:
            relationship_type[constants.PROPERTIES] = utils.merge_sub_dicts(
                overridden_dict=super_type,
                overriding_dict=relationship_type,
                sub_dict_key=constants.PROPERTIES)
            for interfaces in [constants.SOURCE_INTERFACES,
                               constants.TARGET_INTERFACES]:
                relationship_type[interfaces] = interfaces_parser. \
                    merge_relationship_type_interfaces(
                        overriding_interfaces=relationship_type[interfaces],
                        overridden_interfaces=super_type[interfaces])

        _validate_relationship_fields(
            rel_obj=relationship_type,
            plugins=plugins,
            rel_name=relationship_type_name,
            resource_base=resource_base)
        relationship_type['name'] = relationship_type_name
        relationship_type[
            constants.TYPE_HIERARCHY] = self.create_type_hierarchy(super_type)
        return relationship_type


class Relationships(types.Types):

    schema = Dict(type=Relationship)


def _validate_relationship_fields(rel_obj, plugins, rel_name, resource_base):
    for interfaces in [constants.SOURCE_INTERFACES,
                       constants.TARGET_INTERFACES]:
        for interface_name, interface in rel_obj[interfaces].items():
            operation.process_interface_operations(
                interface,
                plugins,
                19,
                'Relationship: {0}'.format(rel_name),
                resource_base=resource_base)
