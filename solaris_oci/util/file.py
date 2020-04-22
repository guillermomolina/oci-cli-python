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


import hashlib
import subprocess

def sha256sum_py(file_path):
    # Should be faster with system's sha256
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096),b''):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    return None

def sha256sum(file_path):
    cmd = ['/usr/bin/sha256sum', str(file_path)]
    sha256sum_run = subprocess.run(cmd, capture_output=True)
    if sha256sum_run.returncode == 0:
        sha256sum_stdout = str(sha256sum_run.stdout.decode('utf-8'))
        records = sha256sum_stdout.split(' ')  
        return records[0]
    return None

def tar(tar_file_path, dir_path, compress=False):
    args = '-c'
    if compress:
        args += 'z'
    cmd = ['/usr/gnu/bin/tar', args, '-f', str(tar_file_path)]
    cmd += [ str(f.relative_to(dir_path)) for f in dir_path.glob('*') ]
    return subprocess.call(cmd, cwd=dir_path)

def gzip(source_file_path, target_file_path, keep_original=True):
    with target_file_path.open('wb') as target_file:
        cmd = ['/usr/bin/gzip', '-cr', str(source_file_path)]
        status = subprocess.call(cmd, stdout=target_file)
        if status == 0 and not keep_original:
            source_file_path.unlink()
        return status
    return 1
