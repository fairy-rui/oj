#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import ast
import re

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('core/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='Judge',
    version=version,
    license='BSD',
    author='snow',
    description="The online judge core that judges the participant's code and supports distributed judgement.",
    packages=['core', 'core.judgecenter', 'core.judgesite'],
    install_requires=[
        'mysql-connector-python>=2.0.3',
        'pika>=0.9.14',
        'paramiko>=1.16.0',
        'lorun>=1.0.1',
    ],
)