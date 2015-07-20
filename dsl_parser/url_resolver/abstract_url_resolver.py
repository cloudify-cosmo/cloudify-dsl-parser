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


class AbstractUrlResolver(object):
    """
    This class is abstract and should be inherited by concrete
    implementations of URL resolver.
    The only mandatory implementation is of get_user, which is expected
    to return an object that inherits security.models.UserModel
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, url):
        raise NotImplementedError
