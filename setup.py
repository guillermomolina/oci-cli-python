# Copyright 2020, Guillermo Adrián Molina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import codecs
from setuptools import setup

# The following version is parsed by other parts of this package.
# Don't change the format of the line, or the variable name.
package_version = "0.0.2"

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()


setup(
    name='solaris-oci',
    version=package_version,
    url='https://github.com/guillermomolina/solaris-oci',
    author='Guillermo Adrián Molina',
    author_email='guillermomolina@hotmail.com',
    license='Apache License, Version 2.0',
    platforms='All',
    description='Solaris-OCI - Open Container Initiative running on Solaris',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    py_modules=['solaris_oci'],
    packages=['solaris_oci'],
    install_requires=[
        'opencontainers',
        'python-dateutil',
        'humanize'
    ],
    entry_points={
        'console_scripts': [
            'runc = solaris_oci.runc.runc:main',
            'mkimage = solaris_oci.mkimage.mkimage:main',
            'mkrepo = solaris_oci.mkrepo.mkrepo:main',
            'mkrootfs = solaris_oci.mkrootfs.mkrootfs:main',
            'oci = solaris_oci.oci.oci:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Operating System',
    ]
)
