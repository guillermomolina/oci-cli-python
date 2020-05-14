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
import pathlib
import logging
import sys
import tempfile
import shutil
import os
from urllib.request import urlopen
from urllib.parse import urlparse
from oci_spec.image.v1 import ImageConfig
from oci_spec.runtime.v1 import Spec
from oci_api import OCIError
from oci_api.image import Distribution, ImageExistsException

log = logging.getLogger(__name__)

class Import:
    @staticmethod
    def init_parser(image_subparsers, parent_parser):
        parser = image_subparsers.add_parser('import',
            parents=[parent_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Import the contents from a tarball to create a filesystem image',
            help='Import the contents from a tarball')
        parser.add_argument('-m', '--message', 
            help='Set commit message for imported image',
            metavar='string')
        parser.add_argument('-r', '--runc-config', 
            help='path to the runc spec file config.json')
        parser.add_argument('file',
            metavar='file|URL|-',
            help='Name of the file or URL to import, or "-" for the standard input')
        parser.add_argument('image',
            metavar='REPOSITORY[:TAG]',
            nargs='?',
            help='Name of the repository to import to')
  
    def __init__(self, options):
        image_name = options.image
        log.debug('Start importing (%s) to (%s)', options.file, image_name)
        try:
            with tempfile.TemporaryDirectory() as temp_dir_name:
                if options.file == '-':
                    input_file = os.fdopen(sys.stdin.fileno(), 'rb')
                else:
                    try:
                        input_file = urlopen(options.file)
                    except ValueError:
                        input_file = open(options.file, 'rb')
                rootfs_tar_path = pathlib.Path(temp_dir_name, 'rootfs.tar')
                with rootfs_tar_path.open('wb') as output_file:
                    log.debug('Start copying (%s) to (%s)', options.file, str(rootfs_tar_path))
                    shutil.copyfileobj(input_file, output_file)
                    log.debug('Finish copying (%s) to (%s)', options.file, str(rootfs_tar_path))
                if rootfs_tar_path.is_file():
                    distribution = Distribution()
                    environment = None
                    command = None
                    working_dir = None
                    if options.runc_config is not None:
                        config_file_path = pathlib.Path(options.runc_config)
                        if not config_file_path.is_file():
                            OCIError('Runc config file (%s) does not exist' % str(config_file_path))
                        spec = Spec.from_file(config_file_path)
                        process = spec.get('Process')
                        command = process.get('Args')
                        environment = process.get('Env')
                        working_dir = process.get('Cwd')
                    image_config = ImageConfig(
                        env=environment,
                        cmd=command,
                        working_dir=working_dir
                    )
                    image = distribution.import_image(image_name, rootfs_tar_path, image_config)
        except ImageExistsException:
            log.error('Image (%s) already exists' % image_name)
            exit(-1)
        except:
            raise e
            log.error('Could not remove image (%s)' % image_name)
            exit(-1)
        log.debug('Finish importing (%s) to (%s)', options.file, image_name)
