# Solaris-OCI
Open Container Initiative running on Solaris

## Using runc

You should have Solaris 11.4, with solaris-oci brand installed:

### Install the solaris-oci brand
$ sudo pkg install system/zones/brand/brand-solaris-oci

### Create the python 3.7 virtualenv
```
$ virtualenv-3.7 solaris-oci
$ cd solaris-oci
$ . bin/activate
```

### Install the package on the virtualenv
```
$ mkdir src
$ cd src
$ git clone https://github.com/guillermomolina/solaris-oci.git
$ pip install solaris-oci
```

### Create a container (Using standard packages)
```
$ mkdir -p container
$ cd container
$ runc spec
$ sudo mkrootfs .
$ sudo runc run container
@container:~/root$ ^D
$ sudo runc delete container
```

```
$ du -sh rootfs/
1.7G    rootfs/
```

### Using local repo to make smaller containers
```
$ sudo mkrepo
$ mkdir container
$ cd container
$ runc spec
$ sudo mkrootfs -r /var/share/pkg/repositories/solaris-oci .
$ sudo runc run container
@container:~/root$ ^D
$ sudo runc delete container
```

```
$ du -sh rootfs/
49M     rootfs/
```
(Only 49Mb!!!!)

## Usinng oci CLI

### Prepare filesystem for oci

```
$ sudo zfs create -o mountpoint=none -o compress=lz4 rpool/oci
```

### Create an image from container

```
$ cd ~/container
$ sudo mkimage solaris:mytag
```

### List images

```
$ oci image ls
REGISTRY   TAG     IMAGE ID       CREATED        SIZE   
solaris    mytag   8556bb25018f   a minute ago   46.0 MB
```

### Delete an image

```
$ oci image rm solaris:mytag
```


