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

def zfs(command,  arguments=None, options=None):
    cmd = ['/usr/sbin/zfs', command]
    if options is not None:
        for option in options:
            cmd += ['-o', option]
    if arguments is not None:
        cmd += arguments
    return subprocess.call(cmd)

def zfs_create(zfs_name, parent=None, mountpoint=None):
    filesystem = zfs_name
    if parent is not None:
        filesystem = parent + '/' + zfs_name

    # Just debugging, don't fail if already created
    #if(destroy(filesystem, recursive=True) == 0):
    #    print('WARNING: Deleting filesystem (%s) ' % filesystem)

    options = None
    if mountpoint is not None:
        options = ['mountpoint=' + str(mountpoint)]
    if zfs('create', [filesystem], options) == 0:
        return filesystem
    return None

def zfs_set(zfs_name, readonly=None, mountpoint=None):
    if readonly is not None:
        option = 'readonly='
        if readonly:
            option += 'on'
        else:
            option += 'off'
        zfs('set', [option, zfs_name])
    if mountpoint is not None:
        zfs('set', ['mountpoint=' + str(mountpoint), zfs_name])

def zfs_get(zfs_name, property):
    if property == 'all':
        raise NotImplementedError()
    output = subprocess.check_output(['/usr/sbin/zfs', 'get', '-Hp', property, zfs_name])
    value = output.decode('utf-8').split('\t')[2]
    if value == 'on':
        return True
    if value == 'off':
        return False
    if value == '-':
        return None
    try: 
        return int(value)
    except ValueError:
        return value

def zfs_snapshot(zfs_name, filesystem, recursive=False):
    arguments = []
    if recursive is not None:
        arguments.append('-r')
    snapshot = filesystem + '@' + zfs_name
    arguments.append(snapshot)
    if zfs('snapshot', arguments) == 0:
        return snapshot
    return None

def zfs_destroy(zfs_name, recursive=False, synchronous=True):
    arguments = []
    if recursive is not None:
        arguments.append('-r')
    if synchronous is not None:
        arguments.append('-s')
    arguments.append(zfs_name)
    return zfs('destroy', arguments)

def zfs_send(last_snapshot, target_file_path, first_snapshot=None, recursive=False):
    cmd = ['/usr/sbin/zfs', 'send']
    if recursive is not None:
        cmd.append('-R')
    if first_snapshot is not None:
        cmd += ['-I', first_snapshot]
    cmd.append(last_snapshot)
    with open(target_file_path,'wb') as target_file:
        status = subprocess.call(cmd, stdout=target_file)
        return status
    return None
