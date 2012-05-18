#!/usr/bin/env python
from setuptools import setup, find_packages

VERSION = '1.5.6'

setup(
    name='giftwrap',
    version=VERSION,
    author='prior',
    author_email='mprior@hubspot.com',
    packages=find_packages(),
    url='https://github.com/HubSpot/giftwrap',
    download_url='https://github.com/HubSpot/giftwrap/tarball/v%s'%VERSION,
    license='LICENSE.txt',
    description='Python Api Wrapping Toolset',
    long_description=open('README.rst').read(),
    install_requires=[
        'requests>=0,<1',
        'utilspy>=0,<1',
    ],
    platforms=['any']
)
