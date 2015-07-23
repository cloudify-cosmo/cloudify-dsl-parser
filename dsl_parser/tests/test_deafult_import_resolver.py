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

import urllib2
import mock

import testtools

from dsl_parser.exceptions import DSLParsingLogicException
from dsl_parser.import_resolver.default_import_resolver import \
    DefaultImportResolver

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


class DefaultResolverTests(testtools.TestCase):

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
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[ORIGINAL_V2_URL, ORIGINAL_V1_URL],
            expected_exception_class=DSLParsingLogicException)

    def test_illegal_resolved_url_from_rules(self):
        rules = [
            {ORIGINAL_V1_PREFIX: ILLEGAL_URL_PREFIX}
        ]
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=rules,
            expected_urls_to_resolve=[ILLEGAL_URL, ORIGINAL_V1_URL],
            expected_exception_class=DSLParsingLogicException)

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
            expected_exception_class=DSLParsingLogicException)

    def test_no_rule_matches_illegal_url(self):
        rules = [
            {'prefix1': VALID_V1_PREFIX},
            {'prefix2': VALID_V2_PREFIX}
        ]
        self._test_default_resolver(
            import_url=ILLEGAL_URL, rules=rules,
            expected_urls_to_resolve=[ILLEGAL_URL],
            expected_exception_class=DSLParsingLogicException)

    def test_no_rules(self):
        self._test_default_resolver(
            import_url=VALID_V1_URL, rules=[],
            expected_urls_to_resolve=[VALID_V1_URL])

    def test_no_rules_not_accesible_url(self):
        self._test_default_resolver(
            import_url=ORIGINAL_V1_URL, rules=[],
            expected_urls_to_resolve=[ORIGINAL_V1_URL],
            expected_exception_class=DSLParsingLogicException)

    def test_no_rules_illegal_url(self):
        self._test_default_resolver(
            import_url=ILLEGAL_URL, rules=[],
            expected_urls_to_resolve=[ILLEGAL_URL],
            expected_exception_class=DSLParsingLogicException)

    def _test_default_resolver(self, import_url, rules,
                               expected_urls_to_resolve=[],
                               expected_exception_class=None):

        urls_to_resolve = []

        def mock_urlopen(url):
            urls_to_resolve.append(url)
            if url in [ORIGINAL_V1_URL, ORIGINAL_V2_URL, INVALID_V1_URL]:
                raise urllib2.URLError('invalid url: {0}'.format(url))
            elif url == ILLEGAL_URL:
                raise ValueError('unknown url type: {0}'.format(url))
            elif url in [VALID_V1_URL, VALID_V2_URL]:
                return mock.MagicMock()

        resolver = DefaultImportResolver(rules=rules)
        with mock.patch('urllib2.urlopen', new=mock_urlopen):
            if not expected_exception_class:
                resolver.resolve(import_url=import_url)
            else:
                self.assertRaises(
                    DSLParsingLogicException, resolver.resolve, import_url)

        self.assertEqual(len(expected_urls_to_resolve), len(urls_to_resolve))
        for resolved_url in expected_urls_to_resolve:
            self.assertIn(resolved_url, urls_to_resolve)
