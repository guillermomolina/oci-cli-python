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


import json
import argparse
from solaris_oci.oci import OCIError
from solaris_oci.oci.runtime import Runtime

class Remove:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('rm',
            parents=[parent_parser],
            aliases=['remove'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Remove one or more containers',
            help='Remove one or more containers')
        parser.add_argument('container',
            nargs='+', 
            metavar='CONTAINER',
            help='Name of the container to remove')
 
    def __init__(self, options):
        runtime = Runtime()
        for container_ref in options.container:
            try:
                runtime.remove_container(container_ref)
            except OCIError as e:
                raise e
                print('Could not remove container (%s)' % container_ref)
