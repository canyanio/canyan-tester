#!/usr/bin/env python3

import setuptools
from setuptools import find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setuptools.setup(
    name='canyantester',
    version='1.2',
    author='Canyan.io',
    author_email='info@canyan.io',
    description='Canyan Testing Tool',
    long_description=readme,
    long_description_content_type="text/markdown",
    license=license,
    url='https://www.canyan.io/',
    install_requires=[
        'Click>=7.0',
        'PyYAML>=3.13',
        'dotty-dict>=1.2.1',
        'requests>=2.22.0',
    ],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    entry_points="""
        [console_scripts]
        canyantester=canyantester:canyantester
    """,
)
