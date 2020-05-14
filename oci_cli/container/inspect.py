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


import json
import argparse
import logging
from oci_api.runtime import Runtime, ContainerUnknownException

log = logging.getLogger(__name__)

class Inspect:
    @staticmethod
    def init_parser(container_subparsers, parent_parser):
        parser = container_subparsers.add_parser('inspect',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Display detailed information on one or more containers',
            help='Display detailed information on one or more containers')
        parser.add_argument('container',
            nargs='+', 
            metavar='CONTAINER',
            help='Name of the container to inspect')
 
    def __init__(self, options):
        runtime = Runtime()
        for container_ref in options.container:
            try:
                container = runtime.get_container(container_ref)
                container_json = container.config.to_dict(use_real_name=True)
                print(json.dumps(container_json, indent=4, default=str))
            except ContainerUnknownException:
                log.error('Container (%s) does not exist' % container_ref)
                exit(-1)
