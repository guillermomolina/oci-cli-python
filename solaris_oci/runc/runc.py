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
import importlib

from .create import Create
from .delete import Delete
from .kill import Kill
from .list import List
from .run import Run
from .spec import Spec
from .start import Start
from .state import State

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                      argparse.RawDescriptionHelpFormatter):
    pass        

class RunC:
    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description='''   runc - Open Container Initiative runtime

runc is a command line client for running applications packaged according to
the Open Container Initiative (OCI) format and is a compliant implementation of the
Open Container Initiative specification.

runc integrates well with existing process supervisors to provide a production
container runtime environment for applications. It can be used with your
existing process monitoring tools and the container will be spawned as a
direct child of the process supervisor.

Containers are configured using bundles. A bundle for a container is a directory
that includes a specification file named "config.json" and a root filesystem.
The root filesystem contains the contents of the container.

To start a new instance of a container:

    # runc run [ -b bundle ] <container-id>

Where "<container-id>" is your name for the instance of the container that you
are starting. The name you provide for the container instance must be unique on
your host. Providing the bundle directory using "-b" is optional. The default
value for "bundle" is the current directory.''')
        parser.add_argument('--debug',
            help='enable debug output for logging', 
            action='store_true')
        parser.add_argument('--log', 
            help='set the log file path where internal debug information is written',
            metavar='value',
            default='/dev/null')
        parser.add_argument('--log-format', 
            help='set the format used by logs',
            choices=['text', 'json'],
            default='text',
            metavar='value')
        parser.add_argument('--root', 
            help='root directory for storage of container state (this should be located in tmpfs)',
            metavar='value',
            default='/var/run/zones')
        parser.add_argument('--runz', 
            help='path to the runz binary',
            metavar='value',
            default='/usr/lib/brand/solaris-oci/runz')

        command_parser = parser.add_subparsers(
            #title='command',
            dest='command',
            metavar='command',
            required=True)

        command_registry = {
            'create': Create, 
            'delete': Delete, 
            'kill': Kill, 
            'list': List, 
            'run': Run, 
            'spec': Spec, 
            'start': Start,
            'state': State
        }

        for command in command_registry.values():
            command.init_parser(command_parser)
 
        args = parser.parse_args()

        command = command_registry[args.command]
        command(args)

def main():
    RunC()

if __name__ == '__main__':
    main()