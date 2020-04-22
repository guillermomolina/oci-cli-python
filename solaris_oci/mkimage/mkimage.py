import argparse
import pathlib
import tempfile
import json

from solaris_oci.util.file import tar
from solaris_oci.oci.image import Image

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                      argparse.RawDescriptionHelpFormatter):
    pass        

def repository_and_tag(string):
    rt = string.split(':')
    if len(rt) != 2:
        msg = "%r is not <repository name>:<tag name>" % string
        raise argparse.ArgumentTypeError(msg)  
    return rt[0], rt[1]

def error(msg):
    print('mkimage: error: ' + msg)
    exit(-1)

class MKImage:
    def __init__(self):
        parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description='''Creates an open container root file system''')
        parser.add_argument('-D', '--debug',
            help='enable debug output for logging', 
            action='store_true')
        parser.add_argument('-f', '--force',
            help='forcibly initializes the rootfs',
            action='store_true')
        parser.add_argument('-b', '--bundle', 
            help='path to the root of the runc bundle directory',
            default='.')
        parser.add_argument('-o', '--output', 
            help='filename of the output tar file (default: stdout)')
        parser.add_argument('repository_and_tag',
            metavar='REPOSITORY:TAG',
            type=repository_and_tag,
            help='path to the rootfs directory, the rootfs will be <path>/rootfs')
 
        options = parser.parse_args()

        if options.debug:
            import ptvsd
            ptvsd.enable_attach()
            ptvsd.wait_for_attach()

        ''' A RunC bundle has a concrete structure 
            (on Solaris we have an extra "/root" directory in between):
            ./config.json
            ./<config.json:root:path>
            ./<config.json:root:path>/root # <-- Solaris runz only
            ./<config.json:root:path>/root/<actual root filesystem>
        '''

        bundle_path = pathlib.Path(options.bundle)
        if not bundle_path.is_dir():
            error('bundle directory (%s) does not exist' % str(bundle_path))      
        config_json_path = bundle_path.joinpath('config.json')
        if not config_json_path.is_file():
            error('''
config file (%s) does not exist
create it with "runc -b %s spec"''' % 
            (str(config_json_path), str(bundle_path)))
        config_json = None
        with config_json_path.open() as config_json_file:
            config_json = json.load(config_json_file)
        if config_json is None:
            error('could not load config file (%s)' % str(config_json_path))
        if 'root' not in config_json or 'path' not in config_json['root']:
            error('there is no <config.root.path> info in (%s)' % str(config_json_path))
        # Solaris runz needs an extra root to the rootfs path
        rootfs_path = bundle_path.joinpath(config_json['root']['path'], 'root')
        if not rootfs_path.is_dir():
            error('rootfs directory (%s) does not exist' % str(rootfs_path))

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir_path = pathlib.Path(tmp_dir_name)
            layer_tar_path = tmp_dir_path.joinpath('layer.tar')
            if tar(layer_tar_path, rootfs_path) != 0:
                error('could not create layer file (%s) from rootfs directory (%s)'
                    % (str(layer_tar_path), str(rootfs_path)))
            repository, tag = options.repository_and_tag
            image = Image(repository, tag)
            image.create(tmp_dir_path, layer_tar_path, config_json)
            layer_tar_path.unlink()
            output_path = options.output or '-'
            tar(output_path, tmp_dir_path)


def main():
    MKImage()

if __name__ == '__main__':
    main()
