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

class Run:
    @staticmethod
    def init_parser(container_subparsers, parent_parser):
        parser = container_subparsers.add_parser('run',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Run a command in a new container',
            help='Run a command in a new container')
        parser.add_argument('--name', 
            help='Assign a name to the container',
            metavar='string')
        parser.add_argument('--rm',
            help='Automatically remove the container when it exits', 
            action='store_true')
        parser.add_argument('-w', '--workdir', 
            help='Working directory inside the container',
            metavar='string')
        parser.add_argument('image',
            metavar='IMAGE',
            help='Name of the image to base the container on')
        parser.add_argument('cmd',
            nargs=argparse.REMAINDER,
            metavar='[COMMAND [ARG [ARG ...]]]',
            help='Command to run')

    def __init__(self, options):
        runtime = Runtime()
        container = runtime.create_container(
            options.image,
            name=options.name, 
            command=options.cmd,
            workdir=options.workdir)
        container.start()
        if options.rm:
            runtime.remove_container(container.id)