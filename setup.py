#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://pysync_redmine.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='pysync_redmine',
    version='0.0.0',
    description='Sync xml project files to a Redmine deployment',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Salvador Ruiz',
    author_email='sruizr@gmail.com',
    url='https://github.com/sruizr/pysync_redmine',
    packages=[
        'pysync_redmine',
    ],
    package_dir={'pysync_redmine': 'pysync_redmine'},
    include_package_data=True,
    install_requires=['Click'
    ],
    entry_points='''
        [console_scripts]
        sync_redmine=pysync_redmine.sync:run
    ''',
    license='MIT',
    zip_safe=False,
    keywords='pysync_redmine',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)

