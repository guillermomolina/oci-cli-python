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
import pathlib
import tempfile
import logging
from dateutil import parser
from datetime import datetime, timezone
from opencontainers.runtime.v1 import Spec, State
from solaris_oci.oci import oci_config, OCIError
from solaris_oci.util import generate_random_sha256, digest_to_id, id_to_digest
from solaris_oci.util.runc import runc_create, runc_delete, runc_exec, \
    runc_start
from solaris_oci.util.file import rm
from solaris_oci.oci.image import Distribution, Layer

log = logging.getLogger(__name__)

class Container():
    def __init__(self, id=None):
        log.debug('Creating instance of %s(%s)' % (type(self).__name__, id or ''))
        self.id = id
        self.runc_id = None
        self.name = None 
        self.create_time = None
        self.config = None
        self.image = None
        self.layer = None
        self.load()

    @property
    def state_change_time(self):
        if self.id is not None:
            zones_path = pathlib.Path('/var/run/zones/state')
            state_file_path = zones_path.joinpath(self.runc_id + '.state')
            if state_file_path.is_file():
                return datetime.fromtimestamp(state_file_path.lstat().st_mtime, 
                    tz=timezone.utc)
        return None

    def status(self):
        container_state = self.state()
        if container_state is not None:
            return container_state.get('Status')
        return None

    def state(self):
        if self.id is not None:
            zones_path = pathlib.Path('/var/run/zones/state')
            state_file_path = zones_path.joinpath(self.runc_id + '.state')
            if state_file_path.is_file():
                return State.from_file(state_file_path)
            container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
            return State(
                id=self.runc_id,
                status='exited',
                bundlepath=str(container_path)
            )
        return None

    def load(self):
        if self.id is not None:
            container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
            container_file_path = container_path.joinpath('container.json')
            with container_file_path.open() as container_file:
                container = json.load(container_file)
                self.runc_id = container['runc_id']
                self.name = container['name']
                self.create_time = parser.isoparse(container['create_time'])
                self.load_image(container['image_id'])
                self.load_layer(container['diff_id'])
                self.load_config()
    
    def load_config(self):
        if self.id is not None:
            container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
            config_file_path = container_path.joinpath('config.json')
            if config_file_path.is_file():
                self.config = Spec.from_file(config_file_path)

    def load_layer(self, diff_id):
        if self.id is not None:
            layer = Layer(diff_id, self.id)
            self.layer = layer

    def load_image(self, image_ref):
        distribution = Distribution()
        image = distribution.get_image(image_ref)
        self.image = image

    def save(self):
        if self.id is None:
            raise OCIError('Can not save container, unknown id')
        container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
        if not container_path.is_dir():
            container_path.mkdir(parents=True)
        container_file_path = container_path.joinpath('container.json')
        container = {
            'id': self.id,
            'name': self.name,
            'runc_id': self.runc_id,
            'image_id': self.image.id,
            'diff_id': self.layer.diff_id,
            'create_time': self.create_time.strftime('%Y-%m-%dT%H:%M:%S.%f000Z')
        }
        with container_file_path.open('w') as container_file:
            json.dump(container, container_file, separators=(',', ':'))
        self.save_config()

    def save_config(self):
        if self.config is None:
            raise OCIError('Config is not initialized, can not save container (%s)'
                 % self.id)
        container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
        if not container_path.is_dir():
            container_path.mkdir(parents=True)
        config_file_path = container_path.joinpath('config.json')
        self.config.save(config_file_path)

    def check_runc_id(self):
        # TODO: check if there is no other runc container with id == self.runc_id
        # return True if we are ok to use it, False otherwise
        return True

    def create(self, image_name, name, command=None, workdir=None):
        self.create_time = datetime.utcnow()
        self.load_image(image_name)
        self.name = name
        while True:
            self.id = generate_random_sha256()
            self.runc_id = self.id[:12] # AKA: zonename
            if self.check_runc_id():
                break
        self.create_layer()
        self.create_config(command, workdir)
        self.save()
        self.create_container()
    
    def create_config(self, command=None, workdir=None):
        if self.image is None:
            raise OCIError('Could not create config for container (%s), there is no image'
                % self.id)
        image_config = self.image.config
        if image_config is None:
            raise OCIError('Could not create config for container (%s), there is no image config'
                % self.id)
        image_config_config = image_config.get('Config')
        if image_config is None:
            raise OCIError('Could not create config for container (%s), there is no image config'
                % self.id)
        config_json = {
            'ociVersion': '1.0.0',
            'platform': {
                'os': image_config.get('OS'),
                'arch': image_config.get('Architecture'),
            },
            'hostname': self.runc_id,
            'process': {
                'terminal': True,
                'user': {
                    "uid": 0,
                    "gid": 0
                },
                "args": command or image_config_config.get('Cmd'),
                "env": image_config_config.get('Env'),
                "cwd": workdir or image_config_config.get('WorkingDir')
            },
            "root": {
                "path": str(self.layer.path),
                "readonly": False
            },
            "solaris": {
                "anet": [
                    {}
                ]
            }
        }
        self.config = Spec.from_json(config_json)

    def create_layer(self):
        if self.image is None:
            raise OCIError('Can not create layer witout image for container (%s)', self.id)
        self.layer = Layer(id=self.id, parent=self.image.top_layer())
        self.layer.create_diff()

    def create_container(self):
        container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
        config_file_path = container_path.joinpath('config.json')
        if not config_file_path.is_file():
            raise OCIError('Could not create container (%s), there is no config file'
                % self.id)
        if self.layer is None:
            raise OCIError('Could not create container (%s), there is no layer'
                % self.id)
        runc_create(self.runc_id, container_path)

    def remove(self):
        if self.id is None:
            raise OCIError('Can not remove container, unknown id')
        container_status = self.status
        if container_status != 'exited':
            self.remove_container()
        self.remove_layer()
        container_path = pathlib.Path(oci_config['global']['path'], 'containers', self.id)
        rm(container_path.joinpath('config.json'))
        rm(container_path.joinpath('container.json'))
        self.config = None
        rm(container_path)
        self.runc_id = None
        self.image = None
        self.id = None
        
    def remove_layer(self):
        if self.layer is None:
            raise OCIError('Container (%s) has no layer' % self.id)
        self.layer.remove()
        self.layer = None

    def remove_container(self):
        if self.runc_id is None:
            raise OCIError('Can not remove container, unknown container id')
        container_status = self.status
        force = container_status == 'running'
        if runc_delete(self.runc_id, force) != 0:
            pass 
            #raise OCIError('Could not delete container')

    def exec(self, command, args=None):
        raise NotImplementedError()
        if self.runc_id is None:
            raise OCIError('Container (%s) can not exec commands' % self.id)
        runc_exec(self.runc_id, command, args)

    def start(self):
        container_state = self.state()
        if container_state == 'created' or container_state == 'stopped':
            raise OCIError('Can not start container (%s) in state (%s)' % 
                (self.id, container_state))
        return runc_start(self.runc_id)