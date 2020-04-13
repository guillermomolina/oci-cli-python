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

import sys
import os
import argparse

class Start:
    @staticmethod
    def init_parser(parent_parser, command_parser):
        parser = command_parser.add_parser('start',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='''The start command executes the user defined process in a 
                created container.''',
            help='executes the user defined process in a created container')
        parser.add_argument('container_id',
            help='''name for the instance of the container that you are starting. The
                name you provide for the container instance must be unique on your 
                host.''')

    def __init__(self, options):
        cmd = [options.runz, 'start', options.container_id]
        if options.debug:
            print('running: ' + ' '.join(cmd))
        sys.stdout.flush()
        os.execv(options.runz, cmd)

'''
import sys
import os
import subprocess
from subprocess import Popen, PIPE
import threading

def run(options):
    env = os.environ.copy()
    p = Popen([options.runz, 'start', options.container_id], 
#    p = Popen(['bash', '-i'], 
            stdin=PIPE, 
            stdout=PIPE, 
            stderr=subprocess.STDOUT, 
            shell=False, 
            env=env)
    sys.stdout.write("Started Local Terminal...\r\n\r\n")

    def writeall(p):
        while True:
            data = p.stdout.read(1).decode("utf-8")
            if not data:
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(p,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            _write(p, d.encode())

    except EOFError:
        pass

def _write(process, message):
    process.stdin.write(message)
    process.stdin.flush()
'''