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

from .create import Create
from .inspect import Inspect
from .list import List
from .remove import Remove
from .run import Run
from .start import Start

class Container:
    commands = {
        'create': Create,
        'inspect': Inspect,
        'ls': List,
        'rm': Remove,
        'run': Run,
        'start': Start
    }

    @staticmethod
    def init_parser(oci_subparsers):
        parent_parser = argparse.ArgumentParser(add_help=False)
        container_parser = oci_subparsers.add_parser('container',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Manage containers',
            help='Manage containers')

        container_subparsers = container_parser.add_subparsers(
            dest='subcommand',
            metavar='COMMAND',
            required=True)

        for subcommand in Container.commands.values():
            subcommand.init_parser(container_subparsers, parent_parser)

    def __init__(self, options):
        command = Container.commands[options.subcommand]
        command(options)
