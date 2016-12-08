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

from dsl_parser import utils
from dsl_parser.constants import RESOLVER_IMPLEMENTATION_KEY, \
    RESLOVER_PARAMETERS_KEY
from dsl_parser.import_resolver.abstract_import_resolver import \
    AbstractImportResolver
from dsl_parser.import_resolver.default_import_resolver import \
    DefaultResolverValidationException, DefaultImportResolver, \
    DEFAULT_RESLOVER_RULES_KEY

default_resolver_class_path = "%s:%s" % (
    DefaultImportResolver.__module__, DefaultImportResolver.__name__)


class MockCustomImportResolverException(Exception):
    pass


class CustomImportResolver(AbstractImportResolver):
    def __init__(self, custom_reolver_parameters):
        self.custom_resolver_parameters = custom_reolver_parameters

    def resolve(self, import_url):
        pass


custom_resolver_class_path = "%s:%s" % (
    CustomImportResolver.__module__, CustomImportResolver.__name__)


class CustomImportResolverWithoutInit(AbstractImportResolver):
    def resolve(self, import_url):
        pass


custom_no_init_resolver_class_path = "%s:%s" % (
    CustomImportResolverWithoutInit.__module__,
    CustomImportResolverWithoutInit.__name__)


class FailedToInitializeCustomImportResolver(AbstractImportResolver):
    def __init__(self):
        raise MockCustomImportResolverException('mock exception')

    def resolve(self, import_url):
        pass


failed_custom_resolver_class_path = "%s:%s" % (
    FailedToInitializeCustomImportResolver.__module__,
    FailedToInitializeCustomImportResolver.__name__)


class CreateImportResolverTests(testtools.TestCase):

    def _test_create_import_resolver(self,
                                     resolver_configuration=None,
                                     expected_resolver=None,
                                     expected_params_name=None,
                                     err_msg_regex=None):
        if expected_resolver:
            resolver = utils.create_import_resolver(resolver_configuration)
            self.assertEqual(resolver.__class__, expected_resolver.__class__)
            if expected_params_name:
                self.assertEqual(
                    resolver.__getattribute__(expected_params_name),
                    expected_resolver.__getattribute__(expected_params_name))
        else:
            self.assertRaisesRegexp(utils.ResolverInstantiationError,
                                    err_msg_regex,
                                    utils.create_import_resolver,
                                    resolver_configuration)

    def test_no_configuration_specified(self):
        self._test_create_import_resolver(
            expected_resolver=DefaultImportResolver(),
            expected_params_name=DEFAULT_RESLOVER_RULES_KEY)

    def test_specified_default_class_path_and_params(self):
        parameters = {
            DEFAULT_RESLOVER_RULES_KEY: [{'rules1key': 'rules1value'}]
        }
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: default_resolver_class_path,
            RESLOVER_PARAMETERS_KEY: parameters
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            expected_resolver=DefaultImportResolver(**parameters),
            expected_params_name=DEFAULT_RESLOVER_RULES_KEY)

    def test_specified_default_class_path_no_params(self):
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: default_resolver_class_path
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            expected_resolver=DefaultImportResolver(),
            expected_params_name=DEFAULT_RESLOVER_RULES_KEY)

    def test_specified_params_no_class_path(self):
        parameters = {
            DEFAULT_RESLOVER_RULES_KEY: [{'rules1key': 'rules1value'}]
        }
        resolver_configuration = {
            RESLOVER_PARAMETERS_KEY: parameters
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            expected_resolver=DefaultImportResolver(**parameters),
            expected_params_name=DEFAULT_RESLOVER_RULES_KEY)

    def test_create_custom_resolver(self):
        parameters = {
            'custom_reolver_parameters': {}
        }
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: custom_resolver_class_path,
            RESLOVER_PARAMETERS_KEY: parameters
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            expected_resolver=CustomImportResolver(
                custom_reolver_parameters={}),
            expected_params_name='custom_resolver_parameters')

    def test_create_custom_resolver_without_init(self):
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: custom_no_init_resolver_class_path,
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            expected_resolver=CustomImportResolverWithoutInit()
        )

    def test_failed_to_initialize_default_resolver(self):

        def mock_default_resolver_init(*_):
            raise DefaultResolverValidationException('mock exception')

        resolver_configuration = {
            DEFAULT_RESLOVER_RULES_KEY: ''
        }
        original_init = DefaultImportResolver.__init__
        DefaultImportResolver.__init__ = mock_default_resolver_init
        try:
            self._test_create_import_resolver(
                resolver_configuration=resolver_configuration,
                err_msg_regex='Failed to instantiate resolver '
                              '\({0}\)\. '
                              'mock exception'
                .format(DefaultImportResolver.__name__))
        finally:
            DefaultImportResolver.__init__ = original_init

    def test_failed_to_initialize_custom_resolver(self):
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: failed_custom_resolver_class_path,
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            err_msg_regex='Failed to instantiate resolver '
                          '\({0}\).*mock exception'
            .format(failed_custom_resolver_class_path))

    def test_create_resolver_illegal_params_type(self):
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: default_resolver_class_path,
            RESLOVER_PARAMETERS_KEY: 'wrong parameters type'
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            err_msg_regex='Invalid parameters supplied for the '
                          'resolver \({0}\): parameters must be '
                          'a dictionary and not str'
            .format(default_resolver_class_path))

    def test_create_default_resolver_illegal_params(self):
        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: default_resolver_class_path,
            RESLOVER_PARAMETERS_KEY: {'wrong parameter name': ''}
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            err_msg_regex='Failed to instantiate resolver \({0}\).*'
                          '__init__\(\) got an unexpected keyword argument '
                          '\'wrong parameter name\''
            .format(default_resolver_class_path))

    def test_create_resolver_illegal_class_path(self):

        resolver_configuration = {
            RESOLVER_IMPLEMENTATION_KEY: 'wrong class path',
        }
        self._test_create_import_resolver(
            resolver_configuration=resolver_configuration,
            err_msg_regex='Failed to instantiate resolver '
                          '\(wrong class path\).*Invalid class path')
