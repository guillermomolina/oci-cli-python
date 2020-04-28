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

from .graph import Graph

config = {
    'global': {
        'path': '/var/lib/oci',
        'run_path': '/var/run/oci'
    },
    'images':{
        'path': '/var/lib/oci/images',
        'registry': '/var/lib/oci/images/distribution.json'
    },
    'layers':{
        'path': '/var/lib/oci/layers',
        'registry': '/var/lib/oci/images/registry.json'
    },
    'containers':{
        'path': '/var/lib/oci/containers'
    },
    'graph': {
        'driver': 'zfs',
        'zfs': {
            'filesystem': 'rpool/oci'
        }
    }
}

graph_driver = Graph.driver()