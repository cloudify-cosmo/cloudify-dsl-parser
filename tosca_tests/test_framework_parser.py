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

from testtools import TestCase

from aria.parser.exceptions import (
    DSLParsingSchemaAPIException,
    DSLParsingException,
    ERROR_CODE_ILLEGAL_VALUE_ACCESS,
)
from aria.parser.framework import (
    parse,
    validate_schema_api,
    Element,
    ElementType,
    Leaf,
    Dict,
    List,
    Value,
)


class TestSchemaValidation(TestCase):
    def _assert_validate_schema_failure(self, element_cls):
        self.assertRaises(
            DSLParsingSchemaAPIException,
            validate_schema_api,
            element_cls=element_cls)

    def _assert_parse_successful(self, value, element_cls, strict=True):
        self.assertEqual(parse(
            value=value,
            element_cls=element_cls,
            strict=strict), value)

    def _assert_parse_failure(
            self, value, element_cls, strict=True, error_code=1):
        exc = self.assertRaises(
            DSLParsingException,
            parse,
            value=value,
            element_cls=element_cls,
            strict=strict)
        self.assertEqual(exc.err_code, error_code)

    def test_invalid_schema(self):
        class TestElement(Element):
            schema = 1
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_element_type_schema(self):
        class TestElement(Element):
            schema = ElementType(type=str)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_leaf_element_type_schema1(self):
        class TestElement(Element):
            schema = Leaf(type=1)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_leaf_element_type_schema2(self):
        class TestElement(Element):
            schema = Leaf(type=())
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_leaf_element_type_schema3(self):
        class TestElement(Element):
            schema = Leaf(type=(1,))
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_dict_element_type_schema1(self):
        class TestElement(Element):
            schema = Dict(type=str)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_dict_element_type_schema2(self):
        class TestElement(Element):
            schema = Dict(type=Element)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_dict_element_type_schema3(self):
        class TestElement(Element):
            schema = Dict(type=1)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_list_element_type_schema1(self):
        class TestElement(Element):
            schema = List(type=str)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_list_element_type_schema2(self):
        class TestElement(Element):
            schema = List(type=Element)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_list_element_type_schema3(self):
        class TestElement(Element):
            schema = List(type=1)
        self._assert_validate_schema_failure(TestElement)

    def test_invalid_dict_schema(self):
        def assertion(schema):
            test_element = type('TestElement', (Element,), {'schema': schema})
            self._assert_validate_schema_failure(test_element)

        class TestLeaf(Element):
            schema = Leaf(type=str)

        assertion({1: TestLeaf})
        assertion({'key': Leaf(type=str)})
        assertion({'key': None})
        assertion({'key': 'str'})
        assertion({'key': Element})

    def test_invalid_list_schema1(self):
        class TestList(Element):
            schema = []
        self._assert_validate_schema_failure(TestList)

    def test_invalid_list_schema2(self):
        class TestList(Element):
            schema = [Leaf(type=str), [Leaf(type=int)]]
        self._assert_validate_schema_failure(TestList)

    def test_invalid_list_schema3(self):
        class TestList(Element):
            schema = [1]
        self._assert_validate_schema_failure(TestList)

    def test_primitive_leaf_element_type_schema_validation(self):
        class TestStrLeaf(Element):
            schema = Leaf(type=str)

        self._assert_parse_successful('some_string', TestStrLeaf)
        self._assert_parse_successful(None, TestStrLeaf)
        self._assert_parse_failure(12, TestStrLeaf)

    def test_dict_leaf_element_type_schema_validation(self):
        class TestDictLeaf(Element):
            schema = Leaf(type=dict)

        self._assert_parse_successful({}, TestDictLeaf)
        self._assert_parse_successful({'key': 'value'}, TestDictLeaf)
        self._assert_parse_successful({'key': None}, TestDictLeaf)
        self._assert_parse_successful({1: '1'}, TestDictLeaf)
        self._assert_parse_successful({None: '1'}, TestDictLeaf)
        self._assert_parse_successful(None, TestDictLeaf)
        self._assert_parse_failure(12, TestDictLeaf)

    def test_list_leaf_element_type_schema_validation(self):
        class TestListLeaf(Element):
            schema = Leaf(type=list)

        self._assert_parse_successful([], TestListLeaf)
        self._assert_parse_successful([1], TestListLeaf)
        self._assert_parse_successful(['one'], TestListLeaf)
        self._assert_parse_successful([None], TestListLeaf)
        self._assert_parse_successful(None, TestListLeaf)
        self._assert_parse_failure(12, TestListLeaf)

    def test_multiple_types_leaf_element_type_schema_validation(self):
        def assertion(element_cls):
            self._assert_parse_successful('one', element_cls)
            self._assert_parse_successful(True, element_cls)
            self._assert_parse_successful([1, 'two'], element_cls)
            self._assert_parse_successful(None, element_cls)
            self._assert_parse_failure(12, element_cls)
            self._assert_parse_failure({}, element_cls)

        class TestLeaf1(Element):
            schema = Leaf(type=(str, bool, list))

        class TestLeaf2(Element):
            schema = Leaf(type=[str, bool, list])

        assertion(TestLeaf1)
        assertion(TestLeaf2)

    def test_dict_element_type_schema_validation(self):
        class TestDictValue(Element):
            schema = Leaf(type=str)

        class TestDict(Element):
            schema = Dict(type=TestDictValue)

        self._assert_parse_successful({}, TestDict)
        self._assert_parse_successful({'key': 'value'}, TestDict)
        self._assert_parse_successful({'key': None}, TestDict)
        self._assert_parse_successful(None, TestDict)
        self._assert_parse_failure(12, TestDict)
        self._assert_parse_failure({'key': 12}, TestDict)
        self._assert_parse_failure({12: 'value'}, TestDict)

    def test_list_element_type_schema_validation(self):
        class TestLeaf(Element):
            schema = Leaf(type=str)

        class TestList(Element):
            schema = List(type=TestLeaf)

        self._assert_parse_successful([], TestList)
        self._assert_parse_successful(None, TestList)
        self._assert_parse_successful(['one'], TestList)
        self._assert_parse_failure(1, TestList)
        self._assert_parse_failure([1], TestList)

    def test_dict_schema_validation(self):
        class TestChildElement(Element):
            schema = Leaf(type=str)

        class TestSchemaDict(Element):
            schema = {'key': TestChildElement}

        self._assert_parse_successful({}, TestSchemaDict)
        self._assert_parse_successful({'key': 'value'}, TestSchemaDict)
        self._assert_parse_successful({'key': None}, TestSchemaDict)
        self._assert_parse_successful(None, TestSchemaDict)
        self._assert_parse_failure(12, TestSchemaDict)
        self._assert_parse_failure({'key': 12}, TestSchemaDict)
        self._assert_parse_failure({'other': 'value'}, TestSchemaDict)
        self._assert_parse_failure({'other': 12}, TestSchemaDict)
        self._assert_parse_failure({12: 'value'}, TestSchemaDict, strict=False)

    def test_empty_dict_schema_validation(self):
        class TestElement(Element):
            schema = {}
        self._assert_parse_successful({}, TestElement)
        self._assert_parse_successful(None, TestElement)
        self._assert_parse_successful(
            {'key': 'value'}, TestElement, strict=False)

    def test_list_schema_validation(self):
        class TestChild(Element):
            schema = Leaf(type=int)

        class TestElement(Element):
            schema = [
                Leaf(type=str),
                {'test': TestChild},
            ]
        self._assert_parse_successful('value', TestElement)
        self._assert_parse_successful({'test': 123}, TestElement)
        self._assert_parse_failure(123, TestElement)
        self._assert_parse_failure({'test': 'value'}, TestElement)

    def test_required_value(self):
        class TestElement(Element):
            required = True
            schema = Leaf(type=str)
        self._assert_parse_successful('1', TestElement)
        self._assert_parse_failure(None, TestElement)

    def test_cycle_detection(self):
        def predicate(source, target):
            return source.name != target.name

        class TestChild(Element):
            schema = Leaf(type=str)
            requires = {
                'self': [
                    Value('req', multiple_results=True, predicate=predicate)],
            }

        class TestElement(Element):
            schema = List(type=TestChild)

        self._assert_parse_successful(['1'], TestElement)
        self._assert_parse_failure(['1', '2'], TestElement, error_code=100)

    def test_strict_validation(self):
        class TestLeaf(Element):
            schema = Leaf(type=str)

        class TestElement(Element):
            schema = {'in_schema': TestLeaf}

        value = {'in_schema': 'ok'}
        self._assert_parse_successful(value, TestElement)
        value['not_in_schema'] = 'not ok'
        self._assert_parse_failure(value, TestElement)
        self._assert_parse_successful(value, TestElement, strict=False)
        value['in_schema'] = 1
        self._assert_parse_failure(value, TestElement, strict=False)

    def test_illegal_value_access(self):
        class ChildElement(Element):
            schema = Leaf(type=str)

            def parse(self):
                return self.ancestor(TestElement).value

        class TestElement(Element):
            schema = {'child': ChildElement}

        self._assert_parse_failure(
            {'child': 'value'},
            TestElement,
            error_code=ERROR_CODE_ILLEGAL_VALUE_ACCESS)
