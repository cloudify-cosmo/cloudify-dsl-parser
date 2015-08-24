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

import abc
import contextlib
import urllib2
import time

import requests

from dsl_parser import exceptions

DEFAULT_RETRY_DELAY = 1
DEFAULT_NUMBER_RETRIES = 5
DEFAULT_REQUEST_TIMEOUT = 10


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


def read_import(import_url):
    error_str = 'Import failed: Unable to open import url'
    if import_url.startswith('file:'):
        try:
            with contextlib.closing(urllib2.urlopen(import_url)) as f:
                return f.read()
        except Exception, ex:
            ex = exceptions.DSLParsingLogicException(
                13, '{0} {1}; {2}'.format(error_str, import_url, ex))
            raise ex
    else:
        num_retries = 0
        while True:
            try:
                response = requests.get(import_url,
                                        timeout=DEFAULT_REQUEST_TIMEOUT)
            except requests.ConnectionError as err:
                if num_retries >= DEFAULT_NUMBER_RETRIES:
                    ex = exceptions.DSLParsingLogicException(
                        13, '{0} {1}; {2}'.format(
                            error_str, import_url, err))
                    raise ex
                time.sleep(DEFAULT_RETRY_DELAY)
                num_retries += 1
            except requests.URLRequired as err:
                ex = exceptions.DSLParsingLogicException(
                    13, '{0} {1}; {2}'.format(
                        error_str, import_url, err))
                raise ex
            else:
                if 200 <= response.status_code < 300:
                    return response.text
                else:
                    ex = exceptions.DSLParsingLogicException(
                        13, '{0} {1}; status code: {2}'.format(
                            error_str, import_url, response.status_code))
                    raise ex
