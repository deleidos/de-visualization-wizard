# -*- coding: utf-8 -*-
"""\
This is a python package that builds Word2Vec modules from either
a set of topics or a text or PDF file
It incorporates python-goose and news-corpus-builder
ported to Python 3.x

Leidos licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
from setuptools import setup, find_packages


requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    ]
tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
    ]

setup(
    name='modelerserver',
    version='0.1.5',
    packages=find_packages(),
    py_modules = ['domainmodeler', 'knowledgemodeler', 'mongoaccessor'],
    include_package_data=True,
    author='dana moore',
    author_email='dana.e.moore _at_ leidos.com',
    description='Domain and Knowledge builder functions',
    url='None',
    download_url='None',
    zip_safe=False,
    keywords='corpus, nlp news,extractor,web scrapping, natural language processing'.split(','),
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        "Programming Language :: Python",
        "Framework :: Pyramid",
        'Topic :: Text Processing',
	],
    entry_points="""\
      [paste.app_factory]
      main = modelerserver:main
      """,
)
