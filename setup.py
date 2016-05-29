########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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

import sys
from setuptools import setup, find_packages

_PACKAGE_NAME = 'cloudify-dsl-parser'
_PYTHON_SUPPORTED_VERSIONS = [(2, 6), (2, 7)]

if ((sys.version_info.major, sys.version_info.minor)
        not in _PYTHON_SUPPORTED_VERSIONS):
    raise NotImplementedError(
        '{0} Package support Python version 2.6 & 2.7 Only'.format(
            _PACKAGE_NAME))

try:
    with open('requirements.txt') as requirements:
        install_requires = requirements.readlines()
except IOError:
    install_requires = []

# install_requires = [
#     'PyYAML==3.10',
#     'networkx==1.8.1',
#     'requests==2.7.0',
#     'retrying==1.3.3',
#     'aria',
# ]

try:
    from collections import OrderedDict  # NOQA
except ImportError, e:
    install_requires.append('ordereddict==1.1')

try:
    import importlib  # NOQA
except ImportError:
    install_requires.append('importlib')

setup(
    name=_PACKAGE_NAME,
    version='3.4a5',
    author='Gigaspaces',
    author_email='cosmo-admin@gigaspaces.com',
    packages=find_packages(),
    license='LICENSE',
    description='Cloudify DSL parser',
    zip_safe=False,
    install_requires=install_requires
)
