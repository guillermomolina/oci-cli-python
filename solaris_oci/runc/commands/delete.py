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
import pathlib
import argparse

class Delete:
    @staticmethod
    def init_parser(parent_parser, command_parser):
        parser = command_parser.add_parser('delete',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Delete any resources held by the container often used with detached container.',
            help='delete any resources held by the container often used with detached container')
        parser.add_argument('-f', '--force',
            help='forcibly deletes the container if it is still running (uses SIGKILL)', 
            action='store_true')
        parser.add_argument('container_id',
            help='name for the instance of the container')

    def __init__(self, options):
        cmd = [options.runz, 'delete']
        if options.force:
            cmd.append('-f')
        cmd.append(options.container_id)
        if options.debug:
            print('running: ' + ' '.join(cmd))
        p = subprocess.run(cmd, capture_output=True)
        # BUG "runz delete" always fails, it is a bug in runz
        # do cleanup myself
        root_path = pathlib.Path(options.root)
        for file_path in root_path.glob('**/%s*' % options.container_id):
            if options.debug:
                print('deleting: %s' % file_path)
            file_path.unlink()
#        if p.returncode != 1:
#            print(p.stderr.decode('utf-8').rstrip('\r\n'))
        exit(p.returncode)
