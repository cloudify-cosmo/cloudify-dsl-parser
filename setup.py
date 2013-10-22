__author__ = 'elip'

from setuptools import setup

COSMO_CELERY_VERSION = "0.1.1"
COSMO_CELERY_BRANCH = "develop"
COSMO_CELERY = "https://github.com/CloudifySource/cosmo-celery-common/tarball/{0}".format(COSMO_CELERY_BRANCH)

setup(
    name='cosmo-plugin-dsl-parser',
    version='0.1.4',
    author='elip',
    author_email='elip@gigaspaces.com',
    packages=['dsl_parser'],
    license='LICENSE',
    description='Plugin for transforming recipe DSLs',
    zip_safe=False,
    install_requires=[
        "cosmo-celery-common"
    ],

    dependency_links=["{0}#egg=cosmo-celery-common-{1}".format(COSMO_CELERY, COSMO_CELERY_VERSION)]
)