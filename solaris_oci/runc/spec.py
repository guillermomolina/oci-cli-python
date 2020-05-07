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

from opencontainers.runtime.v1 import  Spec as Config, Platform, Process, \
    Root, User, Solaris, SolarisAnet, Linux, Windows
from solaris_oci.util import operating_system, architecture

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

        platform_os = operating_system()
        platform = Platform(
            os=platform_os,
            arch=architecture()
        )
        process = Process(
            terminal=True,
            user=User(
                uid=0,
                gid=0
            ),
            args=['sh'],
            env=[
                'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                'TERM=xterm'
            ],
            cwd='/'
        )
        root = Root(
            path='rootfs',
            readonly=False
        )

        if platform_os == Solaris:
            solaris = Solaris(
                anet=[
                    SolarisAnet()
                ]
            )
        else:
            solaris=None

        if platform_os == 'Linux':
            linux = Linux()
        else:
            linux = None

        if platform_os == 'Windows':
            windows = Windows()
        else:
            windows = None

        config = Config(
            platform=platform,
            hostname='runc',
            process=process,
            root=root,
            linux=linux,
            solaris=solaris,
            windows=windows
        )

        config.save(config_path, compact=False)
