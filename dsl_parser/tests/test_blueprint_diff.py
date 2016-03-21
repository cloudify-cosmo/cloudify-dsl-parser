########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import unittest

import yaml
from mock import patch


from dsl_parser.blueprint_diff import convert_path_of_keys_to_dict
from dsl_parser.blueprint_diff import add_entry
from dsl_parser.blueprint_diff import path_exists
from dsl_parser.blueprint_diff import get_value
from dsl_parser.blueprint_diff import blueprint_diff
from dsl_parser.blueprint_diff import list_diff

THIS_DIR = os.path.dirname(os.path.dirname(__file__))
TESTS_DIR = os.path.join(THIS_DIR, 'tests')
RESOURCES_DIR = os.path.join(TESTS_DIR, 'resources')

stub_path_of_keys = ['a', 'b', 'c', 'd']
stub_value = 'value'
stub_dictionary = {'a': '1'}


class DiffTestCase(unittest.TestCase):

    def test_convert_path_of_keys_to_dict(self):
        empty_path_of_keys = []
        path_with_one_key = ['a']
        long_path_of_keys = ['a', 'b', 'c']

        empty_dict = {}
        dict_with_one_key = {'a': stub_value}
        nested_dict = {'a': {'b': {'c': stub_value}}}

        self.assertEqual(convert_path_of_keys_to_dict(empty_path_of_keys,
                                                      stub_value),
                         empty_dict
                         )
        self.assertEqual(convert_path_of_keys_to_dict(path_with_one_key,
                                                      stub_value),
                         dict_with_one_key
                         )
        self.assertEqual(convert_path_of_keys_to_dict(long_path_of_keys,
                                                      stub_value),
                         nested_dict)

    @patch('dsl_parser.blueprint_diff.convert_path_of_keys_to_dict')
    def test_add_entry_to_empty_output(self, convert_path_of_keys_mock):

        output = {}

        add_entry(output, stub_path_of_keys, stub_value)

        convert_path_of_keys_mock.assert_called_with(stub_path_of_keys[0:],
                                                     stub_value)

    @patch('dsl_parser.blueprint_diff.convert_path_of_keys_to_dict')
    def test_add_entry_to_output(self, convert_path_of_keys_mock):

        output = {'a': {'b': {'c': 3}, 'd': {'e': 5}}, 'f': 6}
        path_of_keys = ['a', 'b', 'h']
        add_entry(output, path_of_keys, stub_value)

        convert_path_of_keys_mock.assert_called_with(path_of_keys[2:],
                                                     stub_value)

    def test_add_entry_to_output_without_mocking_convert_path_of_keys(self):
        output = {'a': {'b': {'c': 3}}}
        path_of_keys = ['a', 'b', 'h']
        expected_result = {'a': {'b': {'c': 3, 'h': stub_value}}}

        add_entry(output, path_of_keys, stub_value)
        self.assertEqual(output, expected_result)

    def test_path_exists(self):

        output = {'a': {'b': {'c': 3}, 'd': {'e': 5}}, 'f': 6}

        path_not_in_output = ['a', 'b', 'd']
        path_in_output = ['a', 'd']
        path_in_output_deep = ['f']

        self.assertFalse(path_exists(output, path_not_in_output))
        self.assertTrue(path_exists(output, path_in_output))
        self.assertTrue(path_exists(output, path_in_output_deep))

    def test_get_value(self):

        output = {'a': {'b': {'c': 3}, 'd': {'e': [4, 5]}}, 'f': '6'}

        path_a = ['a', 'b', 'c']
        path_b = ['a', 'd', 'e']
        path_c = ['f']

        self.assertEqual(get_value(output, path_a), 3)
        self.assertEqual(get_value(output, path_b), [4, 5])
        self.assertEqual(get_value(output, path_c), '6')

    def _assert_diff_result(self, diff_function,
                            path_old, path_new, path_output):
        with open(path_old) as f_old:
            with open(path_new) as f_new:
                with open(path_output) as f_output:
                    old = yaml.load(f_old)
                    new = yaml.load(f_new)
                    output = yaml.load(f_output)

                    self.assertEqual(diff_function(old, new), output)

    def test_list_diff(self):

        self._assert_diff_result(
            list_diff,
            os.path.join(RESOURCES_DIR, 'list-before.yaml'),
            os.path.join(RESOURCES_DIR, 'list-after.yaml'),
            os.path.join(RESOURCES_DIR, 'list-diff.yaml')
            )

    def test_blueprint_diff(self):

        blueprint_diff_test_paths = [
            (os.path.join(RESOURCES_DIR, 'example-before.yaml'),
             os.path.join(RESOURCES_DIR, 'example-after.yaml'),
             os.path.join(RESOURCES_DIR, 'example-diff.yaml')
             ),
            (os.path.join(RESOURCES_DIR, 'stage1.yaml'),
             os.path.join(RESOURCES_DIR, 'stage2.yaml'),
             os.path.join(RESOURCES_DIR, 'diff-1-2.yaml')
             ),
            (os.path.join(RESOURCES_DIR, 'stage2.yaml'),
             os.path.join(RESOURCES_DIR, 'stage3.yaml'),
             os.path.join(RESOURCES_DIR, 'diff-2-3.yaml')
             ),
            (os.path.join(RESOURCES_DIR, 'stage3.yaml'),
             os.path.join(RESOURCES_DIR, 'stage4.yaml'),
             os.path.join(RESOURCES_DIR, 'diff-3-4.yaml')
             )
        ]

        for paths_tup in blueprint_diff_test_paths:
            self._assert_diff_result(blueprint_diff, *paths_tup)
