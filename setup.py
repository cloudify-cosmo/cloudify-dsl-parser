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


from setuptools import setup


install_requires = [
    'PyYAML==3.10',
    'networkx==1.9.1',
    'requests>=2.7.0,<3.0.0',
    'retrying==1.3.3'
]

try:
    from collections import OrderedDict  # NOQA
except ImportError, e:
    install_requires.append('ordereddict==1.1')

try:
    import importlib  # NOQA
except ImportError:
    install_requires.append('importlib')

setup(
    name='cloudify-dsl-parser',
    version='4.3.1',
    author='Gigaspaces',
    author_email='cosmo-admin@gigaspaces.com',
    packages=['dsl_parser',
              'dsl_parser.interfaces',
              'dsl_parser.framework',
              'dsl_parser.elements',
              'dsl_parser.import_resolver'],
    license='LICENSE',
    description='Cloudify DSL parser',
    zip_safe=False,
    install_requires=install_requires
)
