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

import subprocess
import argparse
import pathlib

from solaris_oci.oci.image import Distribution

class Load:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('load',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Import the contents from a tarball to create a filesystem image',
            help='Import the contents from a tarball')
        parser.add_argument('-m', '--message', 
            help='Set commit message for imported image',
            metavar='string')
        parser.add_argument('file',
            metavar='file|URL|-',
            help='Name of the file or URL to import, or "-" for the standard input')
        parser.add_argument('repository',
            metavar='REPOSITORY[:TAG]',
            nargs='?',
            help='Name of the repository to import to')
  
    def __init__(self, options):
        distribution = Distribution() 
            