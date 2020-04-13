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
import importlib
import subprocess
import pathlib
import shutil
import os

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                      argparse.RawDescriptionHelpFormatter):
    pass        

def get_files_path():
    script_path = pathlib.Path(__file__)
    solaris_oci_path = script_path.parent.parent
    return solaris_oci_path.joinpath('files')

class MKImage:
    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description='''Creates an open container root file system''')
        parser.add_argument('--debug',
            help='enable debug output for logging', 
            action='store_true')
        parser.add_argument('--log', 
            help='set the log file path where internal debug information is written',
            metavar='value',
            default='/dev/null')
        parser.add_argument('--log-format', 
            help='set the format used by logs',
            choices=['text', 'json'],
            default='text',
            metavar='value')
        parser.add_argument('-f', '--force',
            help='forcibly initializes the rootfs',
            action='store_true')
        parser.add_argument('-r',
            help='''uri of the repository with packages to use (system repository
                "pkg publisher solaris" if None specified), you should consider 
                creating a local repository with "mkrepo" for smaller packages,
                then pass "-r /var/share/pkg/repositories/solaris-oci" to use it''',
            dest='repository',
            metavar='repository',
            default='system')
        parser.add_argument('path', 
            help='path to the rootfs directory, the rootfs will be <path>/rootfs')
 
        self.options = parser.parse_args()
        print("ERROR: Use mkrootfs")
        exit(-1)

        path = pathlib.Path(self.options.path).resolve()
        self.root_path = path.joinpath('rootfs/root')
        self.create_rootfs()
        self.install_packages()
        self.create_repository_db()
        if self.options.debug:
            print('changing owner to root:root of: %s' % path)
        for file_path in path.glob('**/*'):
            shutil.chown(file_path, 'root', 'root')
        if self.options.debug:
            print('Done initializing rootfs at: ' + str(self.root_path))

    def create_rootfs(self):
        print('Creating rootfs at: ' + str(self.root_path))
        if self.root_path.exists():
            if self.options.debug:
                print('Already existed rootfs path: ' + str(self.root_path))
            if not self.options.force:
                print('rootfs (%s) already exists, use --force to overwrite' % str(self.root_path))
                return
            if self.options.debug:
                print('deleting: ' + str(self.root_path))
            os.system('rm -rf ' + str(self.root_path))
        '''shutil.copytree('/home/gmolina/Fuentes/containers/var/packages/core-os/proto', 
            self.root_path,
            # dirs_exist_ok=True, # python 3.8
            symlinks=True
        )'''
        print('Done creating rootfs at: ' + str(self.root_path))

    def install_packages(self):
        print('Installing packages at: ' + str(self.root_path))
        cmd = ['/usr/bin/pkg', 'image-create', '-f', '--full', '--zone', 
            '--variant', 'variant.container=true']
        if self.options.repository != 'system':
            cmd += [ '-p', self.options.repository ]
        cmd.append(str(self.root_path))
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        subprocess.run(cmd)

        if self.options.repository == 'system':
            cmd = ['/usr/bin/pkg', '-R', str(self.root_path), 'set-property',
                'use-system-repo', 'true' ]
            if self.options.debug:
                print('running: ' + ' '.join(cmd))
            subprocess.run(cmd)
       
        cmd = ['/usr/bin/pkg', '-R', str(self.root_path), 'install', 
            'solaris-container', 'core-os' ]
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        subprocess.run(cmd)

        root_usr_sbin_init = self.root_path.joinpath('usr/sbin/init')
        print('Copying init script to : ' + str(root_usr_sbin_init))
        init_path = get_files_path().joinpath('init')
        shutil.copyfile(init_path, root_usr_sbin_init)
        root_usr_sbin_init.chmod(0o555)
        print('Done installing packages at: ' + str(self.root_path))

    def create_repository_db(self):
        # zone wont start if no repository.db with an identity service in it
        root_etc_svc_path = self.root_path.joinpath('etc/svc')
        root_etc_svc_path.mkdir(parents=True, exist_ok=True)
        root_etc_svc_repository_db_path = root_etc_svc_path.joinpath('repository.db')
        print('Creating repository.db at: ' + str(root_etc_svc_repository_db_path))
        if root_etc_svc_repository_db_path.exists():
            if self.options.debug:
                print('Already exists repository DB at ' + 
                    str(self.root_etc_svc_repository_db_path))
            if not self.options.force:
                print('Repository db at (%s) already exists, use --force to overwrite' 
                    % str(self.root_etc_svc_repository_db_path))
                return
        root_system_volatile_repository_door_path = \
            self.root_path.joinpath('system/volatile/repository_door')
        files_path = get_files_path()
        env_vars = {
            'SVCCFG_REPOSITORY': str(root_etc_svc_repository_db_path), 
            'SVCCFG_DOOR_PATH': str(root_system_volatile_repository_door_path)
        }
        for file_path in [
                    files_path.joinpath('identity.xml')
                ]:
            cmd = ['/usr/sbin/svccfg']
            if self.options.debug:
                cmd.append('-v')
            cmd += ['import', str(file_path)]
            if self.options.debug:
                print('running: ' + ' '.join(cmd))
            subprocess.run(cmd, env=env_vars)
        print('Done creating repository.db at: ' + str(root_etc_svc_repository_db_path))

def main():
    MKImage()

if __name__ == '__main__':
    main()
