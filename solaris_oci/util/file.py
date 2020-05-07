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
import secrets
import time
#import shutil
import logging
from solaris_oci.oci import OCIError

log = logging.getLogger(__name__)

def sha256sum(file_path):
    cmd = ['/usr/bin/sha256sum', str(file_path)]
    log.debug('Running command: "' + ' '.join(cmd) + '"')
    sha256sum_run = subprocess.run(cmd, capture_output=True)
    if sha256sum_run.returncode == 0:
        sha256sum_stdout = str(sha256sum_run.stdout.decode('utf-8'))
        records = sha256sum_stdout.split(' ')  
        return records[0]
    return None

def tar(dir_path, tar_file_path=None, compress=False):
    args = '-c'
    if compress:
        args += 'z'
    if tar_file_path is None:
        tar_file_path_str = '-'
    else:
        tar_file_path_str = str(tar_file_path)
    cmd = ['/usr/gnu/bin/tar', args, '-f', tar_file_path_str]
    cmd += [ str(f.relative_to(dir_path)) for f in dir_path.glob('*') ]
    log.debug('Running command: "cd ' + str(dir_path) + ';' + ' '.join(cmd) + '"')
    return subprocess.call(cmd, cwd=dir_path)

def untar(dir_path, tar_file_path=None, tar_file=None):
    if tar_file_path is not None:
        tar_file_path_str = str(tar_file_path)
        stdin = None
    elif tar_file is not None:
        tar_file_path_str = '-'
        stdin = tar_file
    else:
        raise OCIError('untar error either tar_file_path or tar_file is needed')
    cmd = ['/usr/gnu/bin/tar', '-x', '-f', tar_file_path_str]
    log.debug('Running command: "cd ' + str(dir_path) + ';' + ' '.join(cmd) + '"')
    return subprocess.call(cmd, cwd=dir_path, stdin=stdin)

def compress(file_path, method='gz', 
    parallel=True, keep_original=False):

    commands  = {
        'xz': ['/usr/bin/xz'],
        'gz': ['/usr/bin/gzip'],
        'bz2': ['/usr/bin/bzip2'],
        'lz': ['/usr/bin/lzma']
    }

    parallel_commands = {
        'gz': ['/usr/bin/pigz'],
        'xz': ['/usr/bin/xz', '-T', '0'],
    }
    if parallel:
        cmd = parallel_commands.get(method, None)
    else:
        cmd = commands.get(method, None)
    if cmd is None:
        raise OCIError('method (%s) not supported' % method)

    if keep_original:
        cmd.append('--keep')
        
    cmd.append(str(file_path))
    log.debug('Running command: "' + ' '.join(cmd) + '"')
    return subprocess.call(cmd)

def du(dir_name):
    cmd = ['/usr/gnu/bin/du', '-bs', str(dir_name)]
    log.debug('Running command: "' + ' '.join(cmd) + '"')
    output = subprocess.check_output(cmd)
    value = output.decode('utf-8').split()[0]
    return int(value)
        
def rm(file_name, retries=5, sleep=1):
    for i in range(retries):
        if not file_name.exists():
            return 0
        try:
            if file_name.is_dir():
                log.debug('Running command: "rmdir ' + str(file_name) + '"')
                file_name.rmdir()
            else:
                log.debug('Running command: "rm ' + str(file_name) + '"')
                file_name.unlink()
        except:
            log.exception('Could not delete path (%s) at attempt (%i)' % (
                str(file_name), i))
            time.sleep(sleep)
    return -1

