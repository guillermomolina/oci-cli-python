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
from urllib.request import urlopen
from urllib.parse import urlparse
from opencontainers.image.v1 import ImageConfig
from opencontainers.runtime.v1 import Spec
from solaris_oci.oci import OCIError
from solaris_oci.oci.image import Distribution

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
        log.debug('Start importing (%s) to (%s)', options.file, options.image)
        try:
            if options.file == '-':
                rootfs_file = sys.stdin
            else:
                try:
                    rootfs_file = urlopen(options.file)
                except ValueError:
                    rootfs_file = open(options.file)
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
            image = distribution.create_image(options.image, rootfs_file, image_config)
        except: 
            log.exception('Error, could not create image')   
            exit(-1)
        log.debug('Finish importing (%s) to (%s)', options.file, options.image)
