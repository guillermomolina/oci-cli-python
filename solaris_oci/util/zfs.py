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
import logging

log = logging.getLogger(__name__)

def zfs(command,  arguments=None, options=None):
    cmd = ['/usr/sbin/zfs', command]
    if options is not None:
        for option in options:
            cmd += ['-o', option]
    if arguments is not None:
        cmd += arguments
    with open('/dev/null', 'w') as dev_null:
        log.debug('Running command: "' + ' '.join(cmd) + '"')
        return subprocess.call(cmd, stderr=dev_null)
    return -1

def zfs_create(zfs_name, parent=None, mountpoint=None, compression=False):
    filesystem = zfs_name
    if parent is not None:
        filesystem = parent + '/' + zfs_name

    # Just debugging, don't fail if already created
    #if(destroy(filesystem, recursive=True) == 0):
    #    print('WARNING: Deleting filesystem (%s) ' % filesystem)

    options = []
    if mountpoint is not None:
        options += ['mountpoint=' + str(mountpoint)]
    if compression:
        options.append('compression=lz4')
    if len(options) == 0:
        options = None
    if zfs('create', [filesystem], options) == 0:
        return filesystem
    return None

def zfs_clone(zfs_name, snapshot, parent=None, mountpoint=None):
    filesystem = zfs_name
    if parent is not None:
        filesystem = parent + '/' + zfs_name

    # Just debugging, don't fail if already created
    #if(destroy(filesystem, recursive=True) == 0):
    #    print('WARNING: Deleting filesystem (%s) ' % filesystem)

    options = None
    if mountpoint is not None:
        options = ['mountpoint=' + str(mountpoint)]
    if zfs('clone', [snapshot, filesystem], options) == 0:
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

def value_convert(property_name, value):
    if value == 'on':
        return True
    if value == 'off':
        return False
    if value == '-':
        return None
    if property_name == 'mountpoint':
        return pathlib.Path(value)
    try: 
        return int(value)
    except ValueError:
        return value

def zfs_get(zfs_name, property_name):
    if property_name == 'all':
        raise NotImplementedError()
    cmd = ['/usr/sbin/zfs', 'get', '-Hp', property_name, zfs_name]
    with open('/dev/null', 'w') as dev_null:
        log.debug('Running command: "' + ' '.join(cmd) + '"')
        output = subprocess.check_output(cmd, stderr=dev_null)
        value = output.decode('utf-8').split('\t')[2]
        return value_convert(property_name, value)
    return None

def zfs_snapshot(zfs_name, filesystem, recursive=False):
    arguments = []
    if recursive:
        arguments.append('-r')
    snapshot = filesystem + '@' + zfs_name
    arguments.append(snapshot)
    if zfs('snapshot', arguments) == 0:
        return snapshot
    return None

def zfs_destroy(zfs_name, recursive=False, synchronous=True):
    arguments = []
    if recursive:
        arguments.append('-r')
    if synchronous:
        arguments.append('-s')
    arguments.append(zfs_name)
    return zfs('destroy', arguments)

def zfs_send(last_snapshot, target_file_path, first_snapshot=None, recursive=False):
    cmd = ['/usr/sbin/zfs', 'send']
    if recursive:
        cmd.append('-R')
    if first_snapshot is not None:
        cmd += ['-I', first_snapshot]
    cmd.append(last_snapshot)
    with open('/dev/null', 'w') as dev_null:
        with open(target_file_path,'wb') as target_file:
            log.debug('Running command: "' + ' '.join(cmd) + ' > ' + str(target_file_path) + '"')
            return subprocess.call(cmd, stdout=target_file, stderr=dev_null)
    return None

def zfs_list(zfs_name=None, zfs_type=None, recursive=False,\
        properties=['name', 'used', 'avail', 'refer', 'mountpoint']):
    cmd = ['/usr/sbin/zfs', 'list', '-Hp']
    if recursive:
        cmd.append('-r')   
    if zfs_type is not None and zfs_type in ['all', 'filesystem', 
            'snapshot', 'volume']:
        cmd += ['-t', zfs_type]
    if properties is not None:
        cmd += ['-o', ','.join(properties)]
    if zfs_name is not None:
        cmd.append(zfs_name)
    try:
        with open('/dev/null', 'w') as dev_null:
            filesystems = []
            log.debug('Running command: "' + ' '.join(cmd) + '"')
            output = subprocess.check_output(cmd, stderr=dev_null)
            for line in output.decode('utf-8').strip().split('\n'):
                values = line.split('\t')
                filesystem = {}
                for property_name, value in zip(properties, values):
                    filesystem[property_name] = value_convert(property_name, value)
                filesystems.append(filesystem)
            return filesystems
    except:
        return []

def zfs_exists(zfs_name):
    filesystems = zfs_list(zfs_name, zfs_type='all', properties=['name'])
    return len(filesystems) == 1

def zfs_is_filesystem(zfs_name):
    try:
        return zfs_get(zfs_name, 'type') == 'filesystem'
    except:
        return False

def zfs_is_snapshot(zfs_name):
    try:
        return zfs_get(zfs_name, 'type') == 'snapshot'
    except:
        return False
