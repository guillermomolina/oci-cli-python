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
import json
from dateutil import parser
import humanize
from datetime import *

from opencontainers.digest import NewDigestFromEncoded, Parse
from opencontainers.image.v1 import Index

from solaris_oci.util.print import print_table
from solaris_oci.oci.image import Distribution
from solaris_oci.oci import config

class Inspect:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('inspect',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Display detailed information on one or more images',
            help='Display detailed information on one or more images')
        parser.add_argument('image',
            nargs='+',
            metavar='IMAGE',
            help='Name of the image to inspect')
 
    def __init__(self, options):
        self.options = options
        oci_path = pathlib.Path(options.root)

        distribution = Distribution()
        distribution.load()
        images = distribution.images(options.image)
        print(json.dumps(images, indent=4, default=str))
