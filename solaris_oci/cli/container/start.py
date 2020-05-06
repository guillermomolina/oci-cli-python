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

import argparse
from solaris_oci.oci.runtime import Runtime

class Start:
    @staticmethod
    def init_parser(container_subparsers, parent_parser):
        parser = container_subparsers.add_parser('start',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Start one or more stopped containers',
            help='Start one or more stopped containers')
        parser.add_argument('container',
            nargs='*',
            metavar='CONTAINER',
            help='Name, hash or id of the container to start')

    def __init__(self, options):
        runtime = Runtime()
        for container_ref in options.container:
            container = runtime.get_container(container_ref)
            container.start()
