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

class Hydrate:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('hydrate',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Hydrate an image',
            help='Hydrate an image to a filesystem')
  
    def __init__(self, options):
        distribution = self.load_distribution()
        #print(json.dumps(distribution, indent=2))
