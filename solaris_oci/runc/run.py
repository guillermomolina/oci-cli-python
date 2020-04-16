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
import os.path
import pathlib

class Run:
    @staticmethod
    def init_parser(parent_parser):
        parser = parent_parser.add_parser('run',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='''The run command creates an instance of a container
                for a bundle. The bundle is a directory with a specification file
                named "config.json" and a root filesystem. The specification file 
                includes an args parameter. The args parameter is used to specify
                command(s) that get run when the container is started. To change
                the command(s) that get executed on start, edit the args parameter
                of the spec. See "runc spec --help" for more explanation.''',
            help='create and run a container')
        parser.add_argument('-b', '--bundle', 
            help='path to the root of the bundle directory',
            metavar='value',
            default='.')
        parser.add_argument('--console-socket', 
            help='''path to an AF_UNIX socket which will receive a file descriptor
                referencing the master end of the console's pseudoterminal''',
            metavar='value')
        parser.add_argument('-d', '--dettach',
            help='detach from the container\'s process', 
            action='store_true')
        parser.add_argument('--pid-file', 
            help='specify the file to write the process id to',
            metavar='value')
        parser.add_argument('--preserve-fds', 
            help='''Pass N additional file descriptors to the container (stdio
                + $LISTEN_FDS + N in total)''',
            metavar='value',
            type=int,
            default=0)
        parser.add_argument('container_id',
            help='name for the instance of the container')

    def __init__(self, options):
        bundle_path = pathlib.Path(options.bundle).resolve()
        rootfs_path = bundle_path.joinpath('rootfs')
        if not rootfs_path.is_dir():
            print('rootfs (%s) does not exist' % str(rootfs_path))
            exit(1)
        cmd = [options.runz, 'run', options.container_id, str(bundle_path)]
        if options.debug:
            print('running: ' + ' '.join(cmd))
        p = subprocess.run(cmd)
        exit(p.returncode)
