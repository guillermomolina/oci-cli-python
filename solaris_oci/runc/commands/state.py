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
import json
import argparse

from opencontainers.runtime.v1 import State as StateOCI

class State:
    @staticmethod
    def init_parser(parent_parser, command_parser):
        parser = command_parser.add_parser('state',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='''The state command outputs current state information 
                for the instance of a container.''',
            help='output the state of a container')
        parser.add_argument('container_id',
            help='name for the instance of the container')
    
    def __init__(self, options):
        cmd = [options.runz, 'state', options.container_id]
        if options.debug:
            print('running: ' + ' '.join(cmd))
        p = subprocess.run(cmd, capture_output=True)
        if p.returncode == 0:
            state_json = json.loads(p.stdout.decode('utf-8').rstrip('\r\n'))
            state_json['bundle']= state_json.pop('bundlepath')
            state_oci = StateOCI()
            state_oci.load(state_json)
            if state_oci.validate():           
                print(json.dumps(state_json, indent=2))
        else:
            print(p.stderr.decode('utf-8').rstrip('\r\n'))
        exit(p.returncode)
