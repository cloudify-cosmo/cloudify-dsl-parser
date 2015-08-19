########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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

from dsl_parser.tests.abstract_test_parser import AbstractTestParser
from dsl_parser import exceptions
from dsl_parser.exceptions import DSLParsingLogicException
from dsl_parser.tasks import prepare_deployment_plan


class TestDataTypes(AbstractTestParser):

    def test_unknown_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    pair_type:
        properties:
            first:
                type: unknown-type
            second: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, exceptions.ERROR_UNKNOWN_TYPE, DSLParsingLogicException)

    def test_simple(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    pair_type:
        properties:
            first: {}
            second: {}
"""
        self.parse_1_2(yaml)

    def test_definitions(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    pair_type:
        properties:
            first: {}
            second: {}
    pair_of_pairs_type:
        properties:
            first:
                type: pair_type
            second:
                type: pair_type
"""
        self.parse_1_2(yaml)

    def test_infinite_list(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    list_type:
        properties:
            head:
                type: integer
            tail:
                type: list_type
                default:
                    head: 1
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, exceptions.ERROR_CODE_CYCLE, DSLParsingLogicException)

    def test_definitions_with_default_error(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    pair_type:
        properties:
            first: {}
            second: {}
    pair_of_pairs_type:
        properties:
            first:
                type: pair_type
                default:
                    first: 1
                    second: 2
                    third: 4
            second:
                type: pair_type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException)

    def test_unknown_type_in_datatype(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + self.MINIMAL_BLUEPRINT + """
data_types:
    pair_type:
        properties:
            first:
                type: unknown-type
            second: {}
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, exceptions.ERROR_UNKNOWN_TYPE, DSLParsingLogicException)

    def test_nested_validation(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
node_templates:
    n_template:
        type: n_type
        properties:
            n_pair:
                second:
                    first: 4
                    second: invalid_type_value
node_types:
    n_type:
        properties:
            n_pair:
                type: pair_of_pairs_type
data_types:
    pair_type:
        properties:
            first: {}
            second:
                type: integer
    pair_of_pairs_type:
        properties:
            first:
                type: pair_type
                default:
                    first: 1
                    second: 2
            second:
                type: pair_type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_VALUE_DOES_NOT_MATCH_TYPE)

    def test_nested_defaults(self):
        yaml = """
node_types:
    vm_type:
        properties:
            agent:
                type: agent
            agent_name:
                type: string
node_templates:
    vm:
        type: vm_type
        properties:
            agent: {}
            agent_name: { get_property: [SELF, agent, connection, username] }
data_types:
    agent_connection:
        properties:
            username:
                type: string
                default: ubuntu
            key:
                type: string
                default: ~/.ssh/id_rsa

    agent:
        properties:
            connection:
                type: agent_connection
                default: {}
            basedir:
                type: string
                default: /home/
"""
        parsed = prepare_deployment_plan(self.parse_1_2(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('ubuntu', vm['properties']['agent_name'])

    def test_derives(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
node_types:
    vm_type:
        properties:
            agent:
                type: agent
            agent_name:
                type: string
            agent_key:
                type: string
node_templates:
    vm:
        type: vm_type
        properties:
            agent:
                connection:
                    key: /home/ubuntu/id_rsa
            agent_name: { get_property: [SELF, agent, connection, username] }
            agent_key: { get_property: [SELF, agent, connection, key] }
data_types:
    agent_connection:
        properties:
            username:
                type: string
                default: ubuntu
            key:
                type: string
                default: ~/.ssh/id_rsa
    agent:
        derived_from: agent_installer
        properties:
            basedir:
                type: string
                default: /home/
    agent_installer:
        properties:
            connection:
                type: agent_connection
                default: {}
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('ubuntu', vm['properties']['agent_name'])
        self.assertEqual('/home/ubuntu/id_rsa', vm['properties']['agent_key'])

    def test_nested_type_error(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
node_templates:
    node:
        type: node_type
        properties:
            a:
                b:
                    c:
                        d: should_be_int
node_types:
    node_type:
        properties:
            a:
                type: a
data_types:
    a:
        properties:
            b:
                type: b
    b:
        properties:
            c:
                type: c
    c:
        properties:
            d:
                type: integer

"""
        ex = self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_VALUE_DOES_NOT_MATCH_TYPE)
        self.assertIn('a.b.c.d', ex.message)

    def test_unknown_parent(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    a:
        derived_from: b
        properties:
            p:
                type: integer
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_UNKNOWN_TYPE,
            DSLParsingLogicException)

    def test_redefine_primitive(self):
        yaml = self.MINIMAL_BLUEPRINT + """
data_types:
    integer:
        properties:
            p:
                type: string
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_INVALID_TYPE_NAME,
            DSLParsingLogicException)

    def test_subtype_override_field_type(self):
        yaml = """
node_templates:
    node:
        type: node_type
        properties:
            b:
                i: 'redefined from int'
                s: 'to make sure that b really derives from a'
node_types:
    node_type:
        properties:
            b:
                type: b
data_types:
    a:
        properties:
            i:
                type: integer
            s:
                type: string
    b:
        derived_from: a
        properties:
            i:
                type: string
"""
        self.parse_1_2(yaml)

    def test_nested_type_error_in_default(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + self.MINIMAL_BLUEPRINT + """
data_types:
    a:
        properties:
            b:
                type: b
                default:
                    c:
                        d:
                            e: 'should be int'
    b:
        properties:
            c:
                type: c
    c:
        properties:
            d:
                type: d
    d:
        properties:
            e:
                type: integer
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_VALUE_DOES_NOT_MATCH_TYPE)

    def test_nested_merging(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
node_templates:
    node:
        type: node_type
        properties:
            b: {}
node_types:
    node_type:
        properties:
            b:
                type: b
                default:
                    i: 'it will be ignored'
            bb:
                type: b
                default:
                    i: 'it will be used'
data_types:
    a:
        properties:
            i:
                type: integer
            s:
                type: string
                default: 's string'
    b:
        derived_from: a
        properties:
            i:
                type: string
                default: 'i string'
"""
        parsed = prepare_deployment_plan(self.parse(yaml))
        node = self.get_node_by_name(parsed, 'node')
        expected = {
            'b': {
                'i': 'i string',
                's': 's string'
            },
            'bb': {
                'i': 'it will be used',
                's': 's string'
            }
        }
        self.assertEqual(node['properties'], expected)

    def test_version_check(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_1 + self.MINIMAL_BLUEPRINT + """
data_types:
    a:
        properties:
            i:
                type: integer
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml,
            exceptions.ERROR_FEATURE_NOT_SUPPORTED_IN_THIS_VERSION)

    def test_implicit_default_value(self):
        yaml = """
data_types:
    data1:
        properties:
            inner:
                default: inner_default

node_types:
    type1:
        properties:
            prop1:
                type: data1

node_templates:
    node1:
        type: type1
"""
        self.parse_1_2(yaml)
