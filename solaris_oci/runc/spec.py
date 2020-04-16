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
import os.path
import json
import platform

#from opencontainers.runtime.v1 import Spec

class Spec:
    @staticmethod
    def init_parser(parent_parser):
        parser = parent_parser.add_parser('spec',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='''The spec command creates the new specification file named
                "config.json" for the bundle. The spec generated is just a starter
                file. Editing of the spec is required to achieve desired results. 
                For example, the newly generated spec includes an args parameter
                that is initially set to call the "sh" command when the container
                is started. Calling "sh" may work for an ubuntu container or busybox,
                but will not work for containers that do not include the "sh" 
                program.''',
            help='create a new specification file')
        parser.add_argument('-b', '--bundle', 
            help='path to the root of the bundle directory',
            metavar='value',
            default='.')
        parser.add_argument('-f', '--force',
            help='overwrite config.json if it already exists', 
            action='store_true')
        parser.add_argument('--rootless',
            help='generate a configuration for a rootless container', 
            action='store_true')

    def __init__(self, options):
        config_path = options.bundle + '/config.json'
        if os.path.isfile(config_path) and not options.force:
            print ('File config.json exists. Use -f to overwrite')
            exit(1)

        architectures = {
            'sparc': 'sparc64', 
            'i386': 'amd64'
        }

        config = {
            'ociVersion': '1.0.0',
            'platform': {
                'os': 'SunOS',
                'arch': architectures[platform.processor()]
            },
            'hostname': 'runc',
            'process': {
                'terminal': True,
                'user': {
                    'uid': 0,
                    'gid': 0
                },
                'args': [
                    'sh'
                ],
                'env': [
                    'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                    'TERM=xterm'
                ],
                'cwd': '/root'
            },
            'root': {
                'path': 'rootfs',
                'readonly': False
            },
            'solaris': {
                'anet': [
                    {}
                ]
            }
        }

        '''spec = Spec()
        spec.load(config)
        if spec.validate():           
            print (json.dumps(config, indent=8))'''
        with open(config_path, 'w') as config_file:
            json.dump(config, config_file, indent=8)