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
import re

DEBUG=False
#DEBUG=True
if DEBUG:
    import ptvsd
    ptvsd.enable_attach()
    ptvsd.wait_for_attach()

def get_mogrify_files_path():
    script_path = pathlib.Path(__file__)
    solaris_oci_path = script_path.parent.parent
    return solaris_oci_path.joinpath('mogrify')

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                      argparse.RawDescriptionHelpFormatter):
    pass        

class MKRepo:
    def __init__(self):
        self.package_list = [ 
            'group/system/solaris-container',
            'shell/ksh93',
            'system/core-os',
            'system/library',
            'system/library/libc',
            'system/library/math',
            'system/library/security/crypto',
            'system/library/smf',
            'library/zlib',
            'system/linker'
        ]
        parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description='''Creates an open container root file system''')
        parser.add_argument('--debug',
            help='enable debug output for logging', 
            action='store_true')
        parser.add_argument('-f', '--force',
            help='forcibly initializes the rootfs', 
            action='store_true')
        parser.add_argument('-p', '--path', 
            help='path to the root of the repository',
            default='/var/share/pkg/repositories/solaris-oci')
        parser.add_argument('packages',
            nargs='*',
            choices=['all'] + self.package_list,
            default='all',
            metavar='package',
            help='Name of the package to initialize')
 
        self.options = parser.parse_args()

        if 'all' in self.options.packages:
            self.options.packages = self.package_list

        self.repo_path = pathlib.Path(self.options.path).resolve()
        self.create_repository()
        self.update_packages()

        if self.options.debug:
            print('Done initializing repository at: ' + str(self.repo_path))

    def create_repository(self):
        print('Creating repository at: ' + str(self.repo_path))
        cmd = ['/usr/bin/pkgrepo', 'create', str(self.repo_path)]
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        subprocess.run(cmd)
    
    def get_solaris_publisher(self):
        cmd = ['/usr/bin/pkg', 'publisher', '-H']
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        pkg_run = subprocess.run(cmd, capture_output=True)
        if pkg_run.returncode == 0:
            pkg_stdout = str(pkg_run.stdout.decode('utf-8'))
            for line in pkg_stdout.splitlines():
                line = re.sub('\s+',' ',line)
                record = line.split(' ')
                if record[0] == 'solaris' and record[2] == 'online':
                    publisher = record[4]
                    return publisher
        print('There is no online solaris publisher, add one first with:')
        print('"pkg set-publisher -g http://pkg.oracle.com/solaris/release/ solaris"')
        exit(-1)
    
    def get_package_uri(self, package_name, repository='', latest=False):
        package_uri = ''
        cmd = ['/usr/bin/pkg', 'list', '-H', '-v']
        if latest:
            cmd.append('-n')
        if repository != '':
            cmd += ['-g', repository]
        cmd += ['--no-refresh', package_name]
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        pkg_run = subprocess.run(cmd, capture_output=True)
        if pkg_run.returncode == 0:
            pkg_stdout = str(pkg_run.stdout.decode('utf-8'))
            for line in pkg_stdout.splitlines():
                record = line.split(' ')
                package_uri = record[0]
        return package_uri

    def update_packages(self):
        source_repository = self.get_solaris_publisher()
        target_repository = str(self.repo_path)
        if self.options.debug:
            print('source repository: ' + source_repository)
        mogrify_files_path = get_mogrify_files_path()
        for package_name in self.options.packages:
            print('Adding package ' + package_name)
            package_uri = self.get_package_uri(package_name)
            if self.options.debug:
                print('package uri: ' + package_uri)
            if self.get_package_uri(package_name, target_repository) == package_uri:
                if self.options.force:
                    print('Removing package ' + package_name)
                    cmd = ['/usr/bin/pkgrepo', 'remove',
                        '-s', target_repository, package_uri ]
                    if self.options.debug:
                        print('running: ' + ' '.join(cmd))
                    subprocess.call(cmd)
                else:
                    print('Package %s is up to date, nothing done' % package_name)
                    continue
            package_mog_file_path = mogrify_files_path.joinpath('solaris/' 
                + package_name + '.mog')
            all_mog_file_path = mogrify_files_path.joinpath('all.mog')
            if self.options.debug:
                print('mogrify file path: ' + str(package_mog_file_path))
            if package_mog_file_path.is_file() and all_mog_file_path.is_file():
                cmd = ['/usr/bin/pkgrecv',
                    '-s', source_repository,
                    '-d', target_repository,
                    '-c', '/var/run/pkg/cache', 
                    '--mog-file', str(all_mog_file_path),
                    '--mog-file', str(package_mog_file_path),
                    package_uri
                ]
                if self.options.debug:
                    print('running: ' + ' '.join(cmd))
                if subprocess.call(cmd) == 0:
                    print('Done adding package ' + package_name)
                else:
                    print('Error adding package ' + package_name)  
            else:
                print('Error mogrify file does not exists ' + str(mog_file_path))
        print('Refreshing repository at ' + target_repository)
        cmd = ['/usr/bin/pkgrepo', 'refresh', '-s', target_repository]
        if self.options.debug:
            print('running: ' + ' '.join(cmd))
        subprocess.call(cmd)

def main():
    MKRepo()

if __name__ == '__main__':
    main()
