import argparse
import pathlib
import tempfile
import json

from solaris_oci.oci import OCIError
from solaris_oci.util.file import tar
from solaris_oci.oci.image import Distribution

def error(msg):
    print('mkimage: error: ' + msg)
    exit(-1)

class MKImage:
    def __init__(self):
        parser = argparse.ArgumentParser(
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
        #parser.add_argument('-o', '--output', 
        #    help='filename of the output tar file (default: stdout)')
        parser.add_argument('image',
            metavar='IMAGE',
            help='image:tag name of the image (default tag "latest"')
 
        options = parser.parse_args()

        if options.debug:
            import ptvsd
            ptvsd.enable_attach()
            print("Waiting for IDE to attach...")
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
        rootfs_path = bundle_path.joinpath(config_json['root']['path'])
        # Solaris runz needs an extra root to the rootfs path
        # rootfs_path = rootfs_path.joinpath('root')
        if not rootfs_path.is_dir():
            error('rootfs directory (%s) does not exist' % str(rootfs_path))
        #if tag in ['latest']:
        #    error('Tag name (%s) is reserved and can not be used' % tag)

        try:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                tmp_dir_path = pathlib.Path(tmp_dir_name)
                rootfs_tar_path = tmp_dir_path.joinpath('layer.tar')
                if tar(rootfs_path, rootfs_tar_path) != 0:
                    error('could not create layer file (%s) from rootfs directory (%s)'
                        % (str(rootfs_tar_path), str(rootfs_path)))
                distribution = Distribution()
                image = distribution.create_image(options.image, rootfs_tar_path, config_json)
                #tar(image.tag_path.resolve(), options.output)
        except OCIError as e: 
            raise e     
            print('Error, could not create image')   
            exit(-1)

def main():
    MKImage()

if __name__ == '__main__':
    main()
