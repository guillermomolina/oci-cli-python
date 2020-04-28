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

from solaris_oci.oci import config
from .container import Container
from .volume import Volume
from .image import Image
 
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                      argparse.RawDescriptionHelpFormatter):
    pass        

class OCI:
    commands = {
        'container': Container,
        'volume': Volume,
        'image': Image
    }

    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description='A self-sufficient runtime for containers')
        parser.add_argument('-D', '--debug',
            help='Enable debug mode', 
            action='store_true')
        parser.add_argument('-v', '--version',
            help='Print version information and quit', 
            action='store_true')
        parser.add_argument('--root', 
            help='root directory for storage',
            metavar='string',
            default=config['images']['path'])

        oci_subparsers = parser.add_subparsers(
            dest='command',
            metavar='COMMAND',
            required=True)

        for command in OCI.commands.values():
            command.init_parser(oci_subparsers)
 
        options = parser.parse_args()

        if options.debug:
            import ptvsd
            ptvsd.enable_attach()
            ptvsd.wait_for_attach()

        command = OCI.commands[options.command]
        command(options)

def main():
    OCI()

if __name__ == '__main__':
    main()