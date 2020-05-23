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
import humanize
from datetime import datetime, timezone
from oci_api.util.print import print_table
from oci_api.runtime import Runtime

class List:
    @staticmethod
    def init_parser(container_subparsers, parent_parser):
        parser = container_subparsers.add_parser('ls',
            parents=[parent_parser],
            aliases=['ps', 'list'],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='List containers',
            help='List containers')
        parser.add_argument('--no-trunc',
            help='Don\'t truncate output', 
            action='store_true')

    def __init__(self, options):
        runtime = Runtime() 
        containers = []
        for container in runtime.containers.values():
            data = {}
            container_state = container.state()
            container_config = container.config
            container_process = container_config.get('Process')
            container_args = container_process.get('Args') or []
            if options.no_trunc:
                data['container id'] = container.id
            else:
                data['container id'] = container.small_id
            data['image'] = container.image.name
            data['command'] = ' '.join(container_args)
            data['created'] = humanize.naturaltime(datetime.now(tz=timezone.utc) - 
                container.create_time)
            container_status = container_state.get('Status').capitalize()
            container_state_change_time = container.state_change_time
            if container_state_change_time is not None:
                container_status += ' ' + humanize.naturaldelta(
                    datetime.now(tz=timezone.utc) - 
                    container.state_change_time)
            data['status'] = container_status
            data['ports'] = ''
            data['names'] = container.name or ''
            containers.append(data)
        print_table(containers)
