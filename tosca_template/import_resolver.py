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

import abc

import requests
from retrying import retry

from .exceptions import (
    DSLParsingLogicException, DefaultResolverValidationException)

DEFAULT_RETRY_DELAY = 1
MAX_NUMBER_RETRIES = 5
DEFAULT_REQUEST_TIMEOUT = 10

DEFAULT_RESLOVER_RULES_KEY = 'rules'


def read_import(import_url):
    error_str = 'Import failed: Unable to open import url'
    if import_url.startswith('file:'):
        response = requests.get(import_url, stream=True)
        if response.status_code != 200:
            raise DSLParsingLogicException(
                13, '{0} {1}'.format(response.status_code, import_url))
    else:
        number_of_attempts = MAX_NUMBER_RETRIES + 1

        # Defines on which errors we should retry the import.
        def _is_recoverable_error(e):
            return isinstance(e, (requests.ConnectionError, requests.Timeout))

        # Defines on which return values we should retry the import.
        def _is_internal_error(result):
            return hasattr(result, 'status_code') and result.status_code >= 500

        @retry(stop_max_attempt_number=number_of_attempts,
               wait_fixed=DEFAULT_RETRY_DELAY,
               retry_on_exception=_is_recoverable_error,
               retry_on_result=_is_internal_error)
        def get_import():
            response = requests.get(
                import_url, timeout=DEFAULT_REQUEST_TIMEOUT)
            # The response is a valid one, and the content should be returned
            if 200 <= response.status_code < 300:
                return response.text
            # If the response status code is above 500, an internal server
            # error has occurred. The return value would be caught by
            # _is_internal_error (as specified in the decorator), and retried.
            elif response.status_code >= 500:
                return response
            # Any other response should raise an exception.
            else:
                invalid_url_err = DSLParsingLogicException(
                    13, '{0} {1}; status code: {2}'.format(
                        error_str, import_url, response.status_code))
                raise invalid_url_err

        try:
            import_result = get_import()
            # If the error is an internal error only. A custom exception should
            # be raised.
            if _is_internal_error(import_result):
                msg = 'Import failed {0} times, due to internal server error' \
                      '; {1}'.format(number_of_attempts, import_result.text)
                raise DSLParsingLogicException(13, msg)
            return import_result
        # If any ConnectionError, Timeout or URLRequired should rise
        # after the retrying mechanism, a custom exception will be raised.
        except (requests.ConnectionError, requests.Timeout,
                requests.URLRequired) as err:
            raise DSLParsingLogicException(
                13, '{0} {1}; {2}'.format(error_str, import_url, err))


class AbstractImportResolver(object):
    """
    This class is abstract and should be inherited by concrete
    implementations of import resolver.
    The only mandatory implementation is of resolve, which is expected
    to open the import url and return its data.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, import_url):
        raise NotImplementedError

    def fetch_import(self, import_url):
        url_parts = import_url.split(':')
        if url_parts[0] in ['http', 'https', 'ftp']:
            return self.resolve(import_url)
        return read_import(import_url)


class DefaultImportResolver(AbstractImportResolver):
    """
    This class is a default implementation of an import resolver.
    This resolver uses the rules to replace URL's prefix with another prefix
    and tries to resolve the new URL (after the prefix has been replaced).
    If there aren't any rules, none of the rules matches or
    none of the prefix replacements works,
    the resolver will try to use the original URL.

    Each rule in the ``rules`` list is expected to be
    a dictionary with one (key, value) pair which represents
    a prefix and its replacement which can be used to resolve the import url.

    The resolver will go over the rules and for each matching rule
    (its key is a prefix of the url) it will replace the prefix
    with the value and will try to resolve the new url.

    For example:
        The rules list: [
            {'http://prefix1': 'http://prefix1_replacement'},
            {'http://prefix2': 'http://prefix2_replacement1'},
            {'http://prefix2': 'http://prefix2_replacement2'}
        ]
        contains three rules that can be used for resolve URLs that
        starts with 'http://prefix1' and 'http://prefix2'.
        If the url is 'http://prefix2.suffix2.org' than the resolve method
        will find a match in both the second and the third rules.

        It will first try to apply the second rule by replacing the url's
        prefix with the second rule value ('http://prefix2_replacement1')
        and will try to resolve the new url:
        'http://prefix2_replacement1.suffix2.org'.

        In case this url cannot be resolved, it will try to apply
        the third rule by replacing the url's prefix with
        the third rule value ('http://prefix2_replacement2')
        and will try to resolve the url:
        'http://prefix2_replacement2.suffix2.org'.

        If this url, also, cannot be resolved,
        it will try to resolve the original url,
        i.e. http://prefix2.suffix2.org'

        In case that all the resolve attempts will fail,
        a DSLParsingLogicException will be raise.
    """

    def __init__(self, rules=()):
        self.rules = rules
        self._validate_rules()

    def resolve(self, import_url):
        failed_urls = {}
        # trying to find a matching rule that can resolve this url
        for rule in self.rules:
            key = rule.keys()[0]
            value = rule.values()[0]
            prefix = key
            prefix_len = len(key)
            if prefix == import_url[:prefix_len]:
                # found a matching rule
                url_to_resolve = value + import_url[prefix_len:]
                # trying to resolve the resolved_url
                if url_to_resolve not in failed_urls.keys():
                    # there is no point to try to resolve the same url twice
                    try:
                        return read_import(url_to_resolve)
                    except DSLParsingLogicException, ex:
                        # failed to resolve current rule,
                        # continue to the next one
                        failed_urls[url_to_resolve] = str(ex)

        # failed to resolve the url using the rules
        # trying to open the original url
        try:
            return read_import(import_url)
        except DSLParsingLogicException, ex:
            if not self.rules:
                raise
            if not failed_urls:
                # no matching rules
                msg = 'None of the resolver rules {0} was applicable, ' \
                      'failed to resolve the original import url: {1} '\
                    .format(self.rules, ex)
            else:
                # all urls failed to be resolved
                msg = 'Failed to resolve the following urls: {0}. ' \
                      'In addition, failed to resolve the original ' \
                      'import url - {1}'.format(failed_urls, ex)
            ex = DSLParsingLogicException(13, msg)
            ex.failed_import = import_url
            raise ex

    def _validate_rules(self):
        if not isinstance(self.rules, list):
            raise DefaultResolverValidationException(
                'Invalid parameters supplied for the default resolver: '
                'The `{0}` parameter must be a list but it is of type {1}.'
                .format(
                    DEFAULT_RESLOVER_RULES_KEY,
                    type(self.rules).__name__))
        for rule in self.rules:
            if not isinstance(rule, dict):
                raise DefaultResolverValidationException(
                    'Invalid parameters supplied for the default resolver: '
                    'Each rule must be a dictionary but the rule '
                    '[{0}] is of type {1}.'
                    .format(rule, type(rule).__name__))
            keys = rule.keys()
            if not len(keys) == 1:
                raise DefaultResolverValidationException(
                    'Invalid parameters supplied for the default resolver: '
                    'Each rule must be a dictionary with one (key,value) pair '
                    'but the rule [{0}] has {1} keys.'
                    .format(rule, len(keys)))
