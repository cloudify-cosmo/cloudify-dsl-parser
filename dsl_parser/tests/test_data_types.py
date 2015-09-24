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
node_templates:
    vm:
        type: vm_type
        properties:
            agent: {}
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
        parsed = self.parse_1_2(yaml)
        vm = parsed['nodes'][0]
        self.assertEqual(
            'ubuntu',
            vm['properties']['agent']['connection']['username'])

    def test_derives(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
node_types:
    vm_type:
        properties:
            agent:
                type: agent
node_templates:
    vm:
        type: vm_type
        properties:
            agent:
                connection:
                    key: /home/ubuntu/id_rsa
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
        parsed = self.parse(yaml)
        vm = parsed['nodes'][0]
        self.assertEqual(
            'ubuntu',
            vm['properties']['agent']['connection']['username'])
        self.assertEqual(
            '/home/ubuntu/id_rsa',
            vm['properties']['agent']['connection']['key'])

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
                    i: 'it will be used too'
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
        parsed = self.parse(yaml)
        node = self.get_node_by_name(parsed, 'node')
        expected = {
            'b': {
                'i': 'it will be used too',
                's': 's string'
            },
            'bb': {
                'i': 'it will be used',
                's': 's string'
            }
        }
        self.assertEqual(expected, node['properties'])

    def test_complex_nested_merging(self):
        yaml = self.BASIC_VERSION_SECTION_DSL_1_2 + """
data_types:
  data1:
    properties:
      inner:
        type: data1_inner
        default:
          inner3: inner3_override
          inner6:
            inner2_3: inner2_3_override
  data12:
    derived_from: data1
    properties:
      inner:
        type: data1_inner
        default:
          inner4: inner4_override
          inner6:
            inner2_4: inner2_4_override
  data1_inner:
    properties:
      inner1:
        default: inner1_default
      inner2:
        default: inner2_default
      inner3:
        default: inner3_default
      inner4:
        default: inner4_default
      inner5:
        default: inner5_default
      inner6:
        type: data2_inner
        default:
          inner2_2: inner2_2_override
      inner7: {}
  data2_inner:
    properties:
      inner2_1:
        default: inner2_1_default
      inner2_2:
        default: inner2_2_default
      inner2_3:
        default: inner2_3_default
      inner2_4:
        default: inner2_4_default
      inner2_5:
        default: inner2_5_default
      inner2_6:
        default: inner2_6_default
node_types:
  type1:
    properties:
      prop1:
        type: data1
        default:
          inner:
            inner4: inner4_override
            inner6:
              inner2_4: inner2_4_override
  type2:
    derived_from: type1
    properties:
      prop1:
        type: data1
        default:
          inner:
            inner5: inner5_override
            inner6:
              inner2_5: inner2_5_override
            inner7: inner7_override
  type3:
    derived_from: type1
    properties:
      prop1:
        type: data12
        default:
          inner:
            inner5: inner5_override
            inner6:
              inner2_5: inner2_5_override
            inner7: inner7_override

node_templates:
  node1:
    type: type1
    properties:
      prop1:
        inner:
          inner2: inner2_override
          inner6:
            inner2_6: inner2_6_override
          inner7: inner7_override
  node2:
    type: type2
    properties:
      prop1:
        inner:
          inner2: inner2_override
          inner6:
            inner2_6: inner2_6_override
  node3:
    type: type3
    properties:
      prop1:
        inner:
          inner2: inner2_override
          inner6:
            inner2_6: inner2_6_override
"""
        parsed = self.parse(yaml)

        def prop1(node_name):
            return self.get_node_by_name(parsed,
                                         node_name)['properties']['prop1']
        node1_prop = prop1('node1')
        node2_prop = prop1('node2')
        node3_prop = prop1('node3')
        self.assertEqual(
            node1_prop,
            {'inner': {'inner1': 'inner1_default',
                       'inner2': 'inner2_override',
                       'inner3': 'inner3_override',
                       'inner4': 'inner4_override',
                       'inner5': 'inner5_default',
                       'inner7': 'inner7_override',
                       'inner6': {'inner2_1': 'inner2_1_default',
                                  'inner2_2': 'inner2_2_override',
                                  'inner2_3': 'inner2_3_override',
                                  'inner2_4': 'inner2_4_override',
                                  'inner2_5': 'inner2_5_default',
                                  'inner2_6': 'inner2_6_override'}}})
        self.assertEqual(
            node2_prop,
            {'inner': {'inner1': 'inner1_default',
                       'inner2': 'inner2_override',
                       'inner3': 'inner3_override',
                       'inner4': 'inner4_override',
                       'inner5': 'inner5_override',
                       'inner7': 'inner7_override',
                       'inner6': {'inner2_1': 'inner2_1_default',
                                  'inner2_2': 'inner2_2_override',
                                  'inner2_3': 'inner2_3_override',
                                  'inner2_4': 'inner2_4_override',
                                  'inner2_5': 'inner2_5_override',
                                  'inner2_6': 'inner2_6_override'}}})
        self.assertEqual(
            node3_prop,
            {'inner': {'inner1': 'inner1_default',
                       'inner2': 'inner2_override',
                       'inner3': 'inner3_override',
                       'inner4': 'inner4_override',
                       'inner5': 'inner5_override',
                       'inner7': 'inner7_override',
                       'inner6': {'inner2_1': 'inner2_1_default',
                                  'inner2_2': 'inner2_2_override',
                                  'inner2_3': 'inner2_3_override',
                                  'inner2_4': 'inner2_4_override',
                                  'inner2_5': 'inner2_5_override',
                                  'inner2_6': 'inner2_6_override'}}})

    def test_partial_default_validation_in_node_template(self):
        yaml = """
data_types:
  datatype:
    properties:
      prop1: {}
      prop2: {}
node_types:
  type:
    properties:
      prop:
        type: datatype
        default:
          prop1: value
node_templates:
  node:
    type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException, self.parse_1_2)

    def test_additional_fields_validation(self):
        yaml = """
data_types:
  datatype:
    properties:
      prop1:
        required: false
node_types:
  type:
    properties:
      prop:
        type: datatype
        default:
          prop2: value
node_templates:
  node:
    type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 106, DSLParsingLogicException, self.parse_1_2)

    def test_nested_required_false(self):
        yaml = """
data_types:
  a:
    properties:
      b: {}

node_types:
  type:
    properties:
      a:
        type: a
        required: false
node_templates:
  node1:
    type: type
"""
        self._assert_dsl_parsing_exception_error_code(
            yaml, 107, DSLParsingLogicException, self.parse_1_2)

    def test_nested_merge_with_inheritance(self):
        yaml = """
data_types:
  a:
    properties:
      b:
        default: b_default
node_types:
  type:
    properties:
      a:
        type: a
        default:
          b: b_override
  type2:
    derived_from: type
    properties:
      a:
        type: a
node_templates:
  node:
    type: type2
"""
        parsed = self.parse_1_2(yaml)
        node = parsed['nodes'][0]
        self.assertEqual(node['properties']['a']['b'], 'b_override')

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
            exceptions.ERROR_CODE_DSL_DEFINITIONS_VERSION_MISMATCH)

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
        parsed = self.parse_1_2(yaml)
        node1 = parsed['nodes'][0]
        self.assertEqual(node1['properties']['prop1']['inner'],
                         'inner_default')

    def test_imports_merging(self):
        file1 = """
data_types:
    data1:
        properties:
            prop1:
                default: value1
"""
        import_path = self.make_yaml_file(file1)
        yaml = """
imports:
  - {0}
data_types:
    data2:
        properties:
            prop2:
                default: value2
node_types:
    type:
        properties:
            prop1:
                type: data1
            prop2:
                type: data2
node_templates:
    node:
        type: type
""".format(import_path)
        properties = self.parse_1_2(yaml)['nodes'][0]['properties']
        self.assertEqual(properties['prop1']['prop1'], 'value1')
        self.assertEqual(properties['prop2']['prop2'], 'value2')
