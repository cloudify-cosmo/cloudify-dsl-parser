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

import testtools

from dsl_parser import exceptions

from dsl_parser.framework import (parser,
                                  elements,
                                  requirements)


class TestSchemaSchemaValidation(testtools.TestCase):

    def assert_invalid(self, element_cls):
        self.assertRaises(exceptions.DSLParsingSchemaAPIException,
                          parser.validate_schema_api,
                          element_cls=element_cls)

    def test_invalid_schema(self):
        class TestElement(elements.Element):
            schema = 1
        self.assert_invalid(TestElement)

    def test_invalid_element_type_schema(self):
        class TestElement(elements.Element):
            schema = elements.ElementType(type=str)
        self.assert_invalid(TestElement)

    def test_invalid_leaf_element_type_schema1(self):
        class TestElement(elements.Element):
            schema = elements.Leaf(type=1)
        self.assert_invalid(TestElement)

    def test_invalid_leaf_element_type_schema2(self):
        class TestElement(elements.Element):
            schema = elements.Leaf(type=())
        self.assert_invalid(TestElement)

    def test_invalid_leaf_element_type_schema3(self):
        class TestElement(elements.Element):
            schema = elements.Leaf(type=(1,))
        self.assert_invalid(TestElement)

    def test_invalid_dict_element_type_schema1(self):
        class TestElement(elements.Element):
            schema = elements.Dict(type=str)
        self.assert_invalid(TestElement)

    def test_invalid_dict_element_type_schema2(self):
        class TestElement(elements.Element):
            schema = elements.Dict(type=elements.Element)
        self.assert_invalid(TestElement)

    def test_invalid_dict_element_type_schema3(self):
        class TestElement(elements.Element):
            schema = elements.Dict(type=1)
        self.assert_invalid(TestElement)

    def test_invalid_list_element_type_schema1(self):
        class TestElement(elements.Element):
            schema = elements.List(type=str)
        self.assert_invalid(TestElement)

    def test_invalid_list_element_type_schema2(self):
        class TestElement(elements.Element):
            schema = elements.List(type=elements.Element)
        self.assert_invalid(TestElement)

    def test_invalid_list_element_type_schema3(self):
        class TestElement(elements.Element):
            schema = elements.List(type=1)
        self.assert_invalid(TestElement)

    def test_invalid_dict_schema(self):
        def assertion(schema):
            test_element = type('TestElement', (elements.Element,),
                                {'schema': schema})
            self.assert_invalid(test_element)

        class TestLeaf(elements.Element):
            schema = elements.Leaf(type=str)

        assertion({1: TestLeaf})
        assertion({'key': elements.Leaf(type=str)})
        assertion({'key': None})
        assertion({'key': 'str'})
        assertion({'key': elements.Element})

    def test_invalid_list_schema1(self):
        class TestList(elements.Element):
            schema = []
        self.assert_invalid(TestList)

    def test_invalid_list_schema2(self):
        class TestList(elements.Element):
            schema = [
                elements.Leaf(type=str),
                [elements.Leaf(type=int)]
            ]
        self.assert_invalid(TestList)

    def test_invalid_list_schema3(self):
        class TestList(elements.Element):
            schema = [1]
        self.assert_invalid(TestList)


class TestSchemaValidation(testtools.TestCase):

    def assert_valid(self, value, element_cls, strict=True):
        self.assertEqual(parser.parse(value=value,
                                      element_cls=element_cls,
                                      strict=strict),
                         value)

    def assert_invalid(self, value, element_cls, strict=True,
                       error_code=1):
        exc = self.assertRaises(exceptions.DSLParsingException,
                                parser.parse,
                                value=value,
                                element_cls=element_cls,
                                strict=strict)
        self.assertEqual(exc.err_code, error_code)

    def test_primitive_leaf_element_type_schema_validation(self):
        class TestStrLeaf(elements.Element):
            schema = elements.Leaf(type=str)

        self.assert_valid('some_string', TestStrLeaf)
        self.assert_valid(None, TestStrLeaf)
        self.assert_invalid(12, TestStrLeaf)

    def test_dict_leaf_element_type_schema_validation(self):
        class TestDictLeaf(elements.Element):
            schema = elements.Leaf(type=dict)

        self.assert_valid({}, TestDictLeaf)
        self.assert_valid({'key': 'value'}, TestDictLeaf)
        self.assert_valid({'key': None}, TestDictLeaf)
        self.assert_valid({1: '1'}, TestDictLeaf)
        self.assert_valid({None: '1'}, TestDictLeaf)
        self.assert_valid(None, TestDictLeaf)
        self.assert_invalid(12, TestDictLeaf)

    def test_list_leaf_element_type_schema_validation(self):
        class TestListLeaf(elements.Element):
            schema = elements.Leaf(type=list)

        self.assert_valid([], TestListLeaf)
        self.assert_valid([1], TestListLeaf)
        self.assert_valid(['one'], TestListLeaf)
        self.assert_valid([None], TestListLeaf)
        self.assert_valid(None, TestListLeaf)
        self.assert_invalid(12, TestListLeaf)

    def test_multiple_types_leaf_element_type_schema_validation(self):
        def assertion(element_cls):
            self.assert_valid('one', element_cls)
            self.assert_valid(True, element_cls)
            self.assert_valid([1, 'two'], element_cls)
            self.assert_valid(None, element_cls)
            self.assert_invalid(12, element_cls)
            self.assert_invalid({}, element_cls)

        class TestLeaf1(elements.Element):
            schema = elements.Leaf(type=(str, bool, list))

        class TestLeaf2(elements.Element):
            schema = elements.Leaf(type=[str, bool, list])

        assertion(TestLeaf1)
        assertion(TestLeaf2)

    def test_dict_element_type_schema_validation(self):
        class TestDictValue(elements.Element):
            schema = elements.Leaf(type=str)

        class TestDict(elements.Element):
            schema = elements.Dict(type=TestDictValue)

        self.assert_valid({}, TestDict)
        self.assert_valid({'key': 'value'}, TestDict)
        self.assert_valid({'key': None}, TestDict)
        self.assert_valid(None, TestDict)
        self.assert_invalid(12, TestDict)
        self.assert_invalid({'key': 12}, TestDict)
        self.assert_invalid({12: 'value'}, TestDict)

    def test_list_element_type_schema_validation(self):
        class TestLeaf(elements.Element):
            schema = elements.Leaf(type=str)

        class TestList(elements.Element):
            schema = elements.List(type=TestLeaf)

        self.assert_valid([], TestList)
        self.assert_valid(None, TestList)
        self.assert_valid(['one'], TestList)
        self.assert_invalid(1, TestList)
        self.assert_invalid([1], TestList)

    def test_dict_schema_validation(self):
        class TestChildElement(elements.Element):
            schema = elements.Leaf(type=str)

        class TestSchemaDict(elements.Element):
            schema = {
                'key': TestChildElement
            }

        self.assert_valid({}, TestSchemaDict)
        self.assert_valid({'key': 'value'}, TestSchemaDict)
        self.assert_valid({'key': None}, TestSchemaDict)
        self.assert_valid(None, TestSchemaDict)
        self.assert_invalid(12, TestSchemaDict)
        self.assert_invalid({'key': 12}, TestSchemaDict)
        self.assert_invalid({'other': 'value'}, TestSchemaDict)
        self.assert_invalid({'other': 12}, TestSchemaDict)
        self.assert_invalid({12: 'value'}, TestSchemaDict, strict=False)

    def test_empty_dict_schema_validation(self):
        class TestElement(elements.Element):
            schema = {}
        self.assert_valid({}, TestElement)
        self.assert_valid(None, TestElement)
        self.assert_valid({'key': 'value'}, TestElement, strict=False)

    def test_list_schema_validation(self):
        class TestChild(elements.Element):
            schema = elements.Leaf(type=int)

        class TestElement(elements.Element):
            schema = [
                elements.Leaf(type=str),
                {
                    'test': TestChild
                }
            ]
        self.assert_valid('value', TestElement)
        self.assert_valid({'test': 123}, TestElement)
        self.assert_invalid(123, TestElement)
        self.assert_invalid({'test': 'value'}, TestElement)

    def test_required_value(self):
        class TestElement(elements.Element):
            required = True
            schema = elements.Leaf(type=str)
        self.assert_valid('1', TestElement)
        self.assert_invalid(None, TestElement)

    def test_cycle_detection(self):
        def predicate(source, target):
            return source.name != target.name

        class TestChild(elements.Element):
            schema = elements.Leaf(type=str)
            requires = {
                'self': [requirements.Value(
                    'req',
                    multiple_results=True,
                    predicate=predicate)]
            }

        class TestElement(elements.Element):
            schema = elements.List(type=TestChild)

        self.assert_valid(['1'], TestElement)
        self.assert_invalid(['1', '2'], TestElement, error_code=100)

    def test_strict_validation(self):
        class TestLeaf(elements.Element):
            schema = elements.Leaf(type=str)

        class TestElement(elements.Element):
            schema = {
                'in_schema': TestLeaf
            }

        value = {'in_schema': 'ok'}
        self.assert_valid(value, TestElement)
        value['not_in_schema'] = 'not ok'
        self.assert_invalid(value, TestElement)
        self.assert_valid(value, TestElement, strict=False)
        value['in_schema'] = 1
        self.assert_invalid(value, TestElement, strict=False)

    def test_illegal_value_access(self):
        class ChildElement(elements.Element):
            schema = elements.Leaf(type=str)

            def parse(self):
                return self.ancestor(TestElement).value

        class TestElement(elements.Element):
            schema = {
                'child': ChildElement
            }

        self.assert_invalid(
            {'child': 'value'},
            TestElement,
            error_code=exceptions.ERROR_CODE_ILLEGAL_VALUE_ACCESS)
