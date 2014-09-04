# !/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from codecs import open
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'fontname.py'), encoding='utf-8') as f:
    version = f.read()
version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version, re.M)
version = version.group(1)

with open(path.join(here, "README.rst"), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fontname',
    version=version,
    description="A lib for guessing font name",
    long_description=long_description,
    url="https://github.com/Asvel/fontname",
    author="Asvel",
    author_email="fe.asvel@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Fonts",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
    keywords="font fontname freetype SFNT",
    py_modules=['fontname'],
    install_requires=['freetype-py'],
)
