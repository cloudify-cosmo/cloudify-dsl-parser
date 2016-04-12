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

import requests
from requests.exceptions import HTTPError
from retrying import retry

DEFAULT_RETRY_DELAY = 1
DEFAULT_REQUEST_TIMEOUT = 10
MAX_NUMBER_RETRIES = 5


def read_data_from_uri(uri):
    try:
        scheme, path = uri.split('://', 1)
        return _READ_HANDLERS_FROM_URI_SCHEMES[scheme](uri)
    except ValueError:
        return read_from_path(uri)
    except KeyError:
        raise Exception('unknown url type: {0}'.format(uri))


def read_from_path(dsl_file_path):
    dsl_file_path = dsl_file_path.replace('file://', '', 1)
    with open(dsl_file_path, 'r') as f:
        return f.read()


@retry(stop_max_attempt_number=MAX_NUMBER_RETRIES + 1,
       wait_fixed=DEFAULT_RETRY_DELAY)
def read_from_url(dsl_url):
    response = requests.get(dsl_url, stream=True)
    if response.status_code != 200:
        raise HTTPError(
            'status code: {0}, url: {1}'.format(response.status_code, dsl_url),
            response=response)
    return response.raw.read()


_READ_HANDLERS_FROM_URI_SCHEMES = {
    'file': read_from_path,
    'http': read_from_url,
    'https': read_from_url,
}
