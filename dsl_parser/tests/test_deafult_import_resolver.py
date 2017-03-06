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

import mock
import requests

import testtools

from dsl_parser.exceptions import DSLParsingLogicException
from dsl_parser.import_resolver.default_import_resolver import \
    DefaultImportResolver, DefaultResolverValidationException
from dsl_parser.import_resolver.abstract_import_resolver import \
    MAX_NUMBER_RETRIES

ORIGINAL_V1_URL = 'http://www.original_v1.org/cloudify/types.yaml'
ORIGINAL_V1_PREFIX = 'http://www.original_v1.org'
ORIGINAL_V2_URL = 'http://www.original_v2.org/cloudify/types.yaml'
ORIGINAL_V2_PREFIX = 'http://www.original_v2.org'

VALID_V1_URL = 'http://localhost_v1/cloudify/types.yaml'
VALID_V1_PREFIX = 'http://localhost_v1'
VALID_V2_URL = 'http://localhost2/cloudify/types.yaml'
VALID_V2_PREFIX = 'http://localhost_v2'

INVALID_V1_URL = 'http://www.not-exist-url.org/cloudify/types.yaml'
INVALID_URL_PREFIX = 'http://www.not-exist-url.org'

ILLEGAL_URL = 'illegal-url/cloudify/types.yaml'
ILLEGAL_URL_PREFIX = 'illegal-url'
TIMEOUT_URL = 'timeout'
BAD_RESPONSE_CODE_URL = 'bad_response_code'
RETRY_URL = 'retry_url'

RETRY_DELAY = 0


class TestDefaultResolver(testtools.TestCase):

    def test_several_matching_rules(self):
        rules = [
            {'some_other_prefix': VALID_V2_PREFIX},
            {ORIGINAL_V1_PREFIX: INVALID_URL_PREFIX},
            {ORIGINAL_V1_PREFIX: ILLEGAL_URL_PREFIX},
            {ORIGINAL_V1_PREFIX: VALID_V1_PREFIX},
        ]
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[
                INVALID_V1_URL, ILLEGAL_URL, VALID_V1_URL])

    def test_not_accesible_url_from_rules(self):
        rules = [
            {ORIGINAL_V1_PREFIX: ORIGINAL_V2_PREFIX}
        ]
        expected_failed_urls = {
            ORIGINAL_V2_URL:
                'Import failed: Unable to open import url {0}'
                '; invalid url: {0}'.format(ORIGINAL_V2_URL)
        }
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[ORIGINAL_V2_URL, ORIGINAL_V1_URL],
            expected_failure=True,
            partial_err_msg='Failed to resolve the following urls: {0}. '
                            "In addition, failed to resolve the original "
                            "import url - Import failed: "
                            "Unable to open import url {1}"
            .format(str(expected_failed_urls), ORIGINAL_V1_URL))

    def test_illegal_resolved_url_from_rules(self):
        rules = [
            {ORIGINAL_V1_PREFIX: ILLEGAL_URL_PREFIX}
        ]
        expected_failed_urls = {
            ILLEGAL_URL:
                'Import failed: Unable to open import url {0}'
                '; unknown url type: {0}'.format(ILLEGAL_URL)
        }

        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[ILLEGAL_URL, ORIGINAL_V1_URL],
            expected_failure=True,
            partial_err_msg='Failed to resolve the following urls: {0}. '
                            "In addition, failed to resolve the original "
                            "import url - Import failed: "
                            "Unable to open import url {1}"
            .format(str(expected_failed_urls), ORIGINAL_V1_URL))

    def test_no_rule_matches(self):
        rules = [
            {'prefix': VALID_V2_PREFIX}
        ]
        self._test_default_resolver(
            import_url=VALID_V1_URL, rules=rules,
            expected_urls_to_resolve=[VALID_V1_URL])

    def test_no_rule_matches_not_accesible_url(self):
        rules = [
            {'prefix1': VALID_V1_PREFIX},
            {'prefix2': VALID_V2_PREFIX}
        ]
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[ORIGINAL_V1_URL],
            expected_failure=True,
            partial_err_msg="None of the resolver rules {0} was applicable, "
                            "failed to resolve the original import url: "
                            "Import failed: Unable to open import url {1}"
            .format(rules, ORIGINAL_V1_URL))

    def test_no_rule_matches_illegal_url(self):
        rules = [
            {'prefix1': VALID_V1_PREFIX},
            {'prefix2': VALID_V2_PREFIX}
        ]
        self._test_default_resolver(
            import_url=ILLEGAL_URL, rules=rules,
            expected_urls_to_resolve=[ILLEGAL_URL],
            expected_failure=True,
            partial_err_msg="None of the resolver rules {0} was applicable, "
                            "failed to resolve the original import url: "
                            "Import failed: Unable to open import url {1}"
            .format(rules, ILLEGAL_URL))

    def test_timeout(self):
        self._test_default_resolver(
            import_url=TIMEOUT_URL, rules=[],
            expected_urls_to_resolve=[TIMEOUT_URL],
            expected_failure=True,
            partial_err_msg="Timeout")

    def test_bad_response_code(self):
        self._test_default_resolver(
            import_url=BAD_RESPONSE_CODE_URL, rules=[],
            expected_urls_to_resolve=[BAD_RESPONSE_CODE_URL],
            expected_failure=True,
            partial_err_msg="status code: 404")

    def test_no_rules(self):
        self._test_default_resolver(
            import_url=VALID_V1_URL, rules=[],
            expected_urls_to_resolve=[VALID_V1_URL])

    def test_retry(self):
        self._test_default_resolver(
            import_url=RETRY_URL, rules=[],
            expected_urls_to_resolve=[RETRY_URL])

    def test_no_rules_not_accesible_url(self):
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=[],
            expected_urls_to_resolve=[ORIGINAL_V1_URL],
            expected_failure=True,
            partial_err_msg="Unable to open import url {0}"
            .format(ORIGINAL_V1_URL))

    def test_no_rules_illegal_url(self):
        self._test_default_resolver(
            import_url=ILLEGAL_URL, rules=[],
            expected_urls_to_resolve=[ILLEGAL_URL],
            expected_failure=True,
            partial_err_msg="Unable to open import url {0}"
            .format(ILLEGAL_URL))

    def _test_default_resolver(self, import_url, rules,
                               expected_urls_to_resolve=[],
                               expected_failure=False,
                               partial_err_msg=None):

        urls_to_resolve = []
        number_of_attempts = []

        class mock_requests_get(object):

            def __init__(self, url, timeout):
                self.status_code = 200
                self.text = 200
                number_of_attempts.append(1)
                if url not in urls_to_resolve:
                    urls_to_resolve.append(url)
                if url in [ORIGINAL_V1_URL, ORIGINAL_V2_URL, INVALID_V1_URL]:
                    raise requests.URLRequired(
                        'invalid url: {0}'.format(url))
                elif url == ILLEGAL_URL:
                    raise requests.URLRequired(
                        'unknown url type: {0}'.format(
                            url))
                elif url in [VALID_V1_URL, VALID_V2_URL]:
                    return None
                elif url == TIMEOUT_URL:
                    raise requests.ConnectionError(
                        'Timeout while trying to import')
                elif url == BAD_RESPONSE_CODE_URL:
                    self.status_code = 404
                    self.text = 404
                elif url == RETRY_URL:
                    if len(number_of_attempts) < MAX_NUMBER_RETRIES:
                        raise requests.ConnectionError(
                            'Timeout while trying to import')
                    else:
                        return None

        resolver = DefaultImportResolver(rules=rules)
        with mock.patch('requests.get', new=mock_requests_get,
                        create=True):
            with mock.patch(
                    'dsl_parser.import_resolver.abstract_import_resolver.'
                    'DEFAULT_RETRY_DELAY', new=RETRY_DELAY):
                try:
                    resolver.resolve(import_url=import_url)
                    if expected_failure:
                        err_msg = 'resolve should have been failed'
                        if partial_err_msg:
                            err_msg = \
                                '{0} with error message that contains: {1}'\
                                .format(err_msg, partial_err_msg)
                        raise AssertionError(err_msg)
                except DSLParsingLogicException, ex:
                    if not expected_failure:
                        raise ex
                    if partial_err_msg:
                        self.assertIn(partial_err_msg, str(ex))

        self.assertEqual(len(expected_urls_to_resolve), len(urls_to_resolve))
        for resolved_url in expected_urls_to_resolve:
            self.assertIn(resolved_url, urls_to_resolve)
        # expected to be 1 initial attempt + 4 retries
        if import_url == RETRY_URL:
            self.assertEqual(MAX_NUMBER_RETRIES, len(number_of_attempts))
        if import_url == TIMEOUT_URL:
            self.assertEqual(MAX_NUMBER_RETRIES + 1, len(number_of_attempts))


class TestDefaultResolverValidations(testtools.TestCase):

    def test_illegal_default_resolver_rules_type(self):
        # wrong rules configuration - string instead of list
        params = {
            'rules': 'this should be a list'
        }
        try:
            DefaultImportResolver(**params)
        except DefaultResolverValidationException, ex:
            self.assertIn(
                'The `rules` parameter must be a list but it is of type str',
                str(ex))

    def test_illegal_default_resolver_rule_type(self):
        # wrong rule type - should be dictionary
        rule = 'this should be a dict'
        rules = [rule]
        params = {
            'rules': rules
        }
        try:
            DefaultImportResolver(**params)
        except DefaultResolverValidationException, ex:
            self.assertIn(
                'Each rule must be a dictionary but the rule '
                '[{0}] is of type {1}'.format(rule, type(rule).__name__),
                str(ex))

    def test_get_default_resolver_illegal_rule_size(self):
        # wrong rule dictionary size - should be only one pair of key, value
        rules = [{'rule1_1': 'rule1_value1', 'rule1_2': 'rule1_value2'}]
        params = {
            'rules': rules
        }
        try:
            DefaultImportResolver(**params)
        except DefaultResolverValidationException, ex:
            self.assertIn(
                'Each rule must be a dictionary with one (key,value) '
                'pair but the rule {0} has 2 keys'
                .format(rules), str(ex))

    def test_illegal_default_resolver_parameters(self):
        # illegal initialization of the default resolver
        params = {
            'wrong_param_name': ''
        }
        try:
            DefaultImportResolver(**params)
        except TypeError, ex:
            self.assertIn(
                'got an unexpected keyword argument \'wrong_param_name\'',
                str(ex))
