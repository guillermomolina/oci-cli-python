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

class Save:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('save',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Save one or more images to a tar archive (streamed to STDOUT by default)',
            help='Save one or more images to a tar archive')
        parser.add_argument('-o', '--output', 
            help='Write to a file, instead of STDOUT',
            metavar='string')
        parser.add_argument('image',
            nargs='+',
            metavar='IMAGE',
            help='Name of the image to save')
  
    def __init__(self, options):
        distribution = Distribution() 
           