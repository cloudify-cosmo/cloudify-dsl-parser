__author__ = 'elip'

from setuptools import setup

setup(
    name='cosmo-plugin-dsl-parser',
    version='0.3',
    author='elip',
    author_email='elip@gigaspaces.com',
    packages=['dsl_parser'],
    license='LICENSE',
    description='Plugin for transforming recipe DSLs',
    zip_safe=False,
    install_requires=[
        "PyYAML==3.10",
        'jsonschema==2.3.0',
        'networkx==1.8.1'
    ]
)
