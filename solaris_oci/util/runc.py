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

def runc(command,  options=None, arguments=None):
    cmd = ['runc', command]
    if options is not None:
        cmd += options
    if arguments is not None:
        cmd += arguments
    #print(' '.join(cmd))
    with open('/dev/null', 'w') as dev_null:
        return subprocess.call(cmd, stderr=dev_null)
    return -1

def runc_create(container_id, bundle_path=None):
    arguments = [container_id]
    options = None
    if bundle_path is not None:
        options = ['-b', bundle_path]
    return runc('create', options, arguments)

def runc_delete(container_id, force=False):
    arguments = [container_id]
    options = None
    if force:
        options = ['--force']
    return runc('delete', options, arguments)

def runc_exec(container_id, command, args=None):
    raise NotImplementedError()
    arguments = [container_id, command]
    options = None
    if args is not None:
        arguments += args
    return runc('exec', options, arguments)

def runc_start(container_id):
    arguments = [container_id]
    options = None
    return runc('start', options, arguments)
