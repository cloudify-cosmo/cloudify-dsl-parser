#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import contextlib
import logging
import urllib2

from dsl_parser import constants
from dsl_parser import exceptions
from dsl_parser.url_resolver.abstract_url_resolver import AbstractUrlResolver

DEFAULT_RULES = [{'http://www.getcloudify.org': 'http://localhost'}]


class ResolverValidationException(Exception):
    pass


class DefaultUrlResolver(AbstractUrlResolver):
    """
    This class is a default implementation of an URL resolver.
    This resolver replaces URL's prefix with another prefix (using the rules)
    and tries to resolve the URL with all prefix replacements,
    If none of the prefix replacements works,
    the resolver will try to use the original URL.
    """

    def __init__(self, rules=[]):
        # set the rules
        self.rules = rules
        if not rules:
            self.rules = DEFAULT_RULES
        # set the logger
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('DefaultUrlResolver')
        self.logger.debug(
            'initializing the default resolver and validating its rules: {0}'
            .format(self.rules))
        self._validate_rules()

    def resolve(self, url):
        urls = []
        # trying to find a matching rule that can resolve this url
        self.logger.debug('trying to resolve url {0}'.format(url))
        for rule in self.rules:
            key = rule.keys()[0]
            value = rule.values()[0]
            prefix = key
            prefix_len = len(key)
            if prefix == url[:prefix_len]:
                # found a matching rule
                resolved_url = value + url[prefix_len:]
                urls.append(resolved_url)
                # trying to resolve the resolved_url
                try:
                    with contextlib.closing(
                            urllib2.urlopen(resolved_url)) as f:
                        self.logger.info("replacing url '{0}' with '{1}'"
                                         .format(url, resolved_url))
                        return f.read()
                except Exception, ex:
                    self.logger.debug(
                        "Failed to resolve url '{0}'; {1}"
                        .format(resolved_url, ex.message))

        # failed to resolve the url using the rules
        if urls:
            rules_message = "None of the matching rules " \
                            "yielded an accessible url." \
                .format(urls)
        else:
            rules_message = "None of the rules matches the url."
        self.logger.debug("{0}"
                          "Trying to read the original url '{1}'"
                          .format(rules_message, url))
        # trying to open the original url
        try:
            with contextlib.closing(urllib2.urlopen(url)) as f:
                return f.read()
        except Exception, ex:
            ex = exceptions.DSLParsingLogicException(
                13, "Failed to resolve url '{0}' ; {1}"
                .format(url, ex.message))
            ex.failed_import = url
            raise ex

    def _validate_rules(self):
        if not isinstance(self.rules, list):
            raise ResolverValidationException(
                'The `{0}` parameter must be a list but it is of type {1}.'
                .format(
                    constants.DEFAULT_RESLOVER_RULES_KEY,
                    type(self.rules)))
        for rule in self.rules:
            if not isinstance(rule, dict):
                raise ResolverValidationException(
                    'Each rule must be a dictionary but the rule: '
                    '[{0}] is of type {1}.'
                    .format(rule, type(rule)))
            keys = rule.keys()
            if not len(keys) == 1:
                raise ResolverValidationException(
                    'Each rule must be a dictionary with one (key,value) pair '
                    'but the rule: [{0}] has {1} keys.'
                    .format(rule, len(keys)))
