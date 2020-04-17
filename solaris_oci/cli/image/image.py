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

from .hydrate import Hydrate
from .inspect import Inspect
from .list import List

'''
image -> repository
tag -> index
'''

class Image:
    commands = {
        'hydrate': Hydrate,
        'inspect': Inspect,
        'ls': List
    }

    @staticmethod
    def init_parser(oci_subparsers):
        parent_parser = argparse.ArgumentParser(add_help=False)
        image_parser = oci_subparsers.add_parser('image',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Manage images',
            help='Manage images')

        image_subparsers = image_parser.add_subparsers(
            dest='subcommand',
            metavar='COMMAND',
            required=True)

        for subcommand in Image.commands.values():
            subcommand.init_parser(image_subparsers, parent_parser)

    def __init__(self, options):
        command = Image.commands[options.subcommand]
        command(options)
