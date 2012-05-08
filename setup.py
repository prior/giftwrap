#!/usr/bin/env python
from distutils.core import setup

VERSION = '1.5.3'

setup(
    name='giftwrap',
    version=VERSION,
    description='Python Api Wraping Toolset',
    author='Michael Prior',
    author_email='prior@cracklabs.com',
    url='https://github.com/prior/giftwrap',
    download_url='https://github.com/prior/giftwrap/tarball/v%s'%VERSION,
    packages=['giftwrap','giftwrap.exchanges','giftwrap.test'],
)
