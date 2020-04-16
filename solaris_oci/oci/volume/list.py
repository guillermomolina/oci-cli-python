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

class List:
    @staticmethod
    def init_parser(volume_subparsers, parent_parser):
        parser = volume_subparsers.add_parser('ls',
            parents=[parent_parser],
            aliases=['list'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='List volumes',
            help='List volumes')
    
    def __init__(self, options):
        pass