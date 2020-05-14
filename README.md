# OCI CLI

Open Container Initiative - Command Line Interface

## Using runc

You should have Solaris 11.4, with solaris-oci brand installed:

### Install the solaris-oci brand

```
$ sudo pkg install system/zones/brand/brand-solaris-oci
```

### Create the python 3.7 virtualenv

```
$ virtualenv-3.7 oci
$ cd oci
$ . bin/activate
```

### Install the package on the virtualenv

```
$ mkdir src
$ cd src
$ git clone -b oci-spec https://github.com/guillermomolina/oci-spec-python.git
$ pip install oci-spec-python
$ git clone https://github.com/guillermomolina/oci-api-python.git
$ pip install oci-api-python
$ git clone https://github.com/guillermomolina/oci-solaris-python.git
$ pip install oci-solaris-python
$ git clone https://github.com/guillermomolina/oci-cli-python.git
$ pip install oci-cli-python
```

## Usinng oci CLI

### Image commands

#### Import an image from runc bundle

```
$ cd ~/container/rootfs
$ tar cf - . | oci image import -r ../config.json - solaris:small
```

#### Save an image to an oci tar file

```
$ oci image save -o /tmp/solaris_small.tar solaris:small
```

#### Delete an image

```
$ oci image rm solaris:small
```

#### Load an image from an oci tar file

```
$ sudo oci image load -i /tmp/solaris_small.tar solaris:small
```

#### List images

```
$ oci image ls
REGISTRY   TAG     IMAGE ID       CREATED        SIZE   
solaris    small   8556bb25018f   a minute ago   46.0 MB
```


### Container commands

#### Create, run and delete a container

```
$ sudo oci container run --name mycontainer --rm -w / solaris ls -la
total 1008
drwxr-xr-x  15 root     root          19 Apr 19 01:32 .
drwxr-xr-x  15 root     root          19 Apr 19 01:32 ..
-rwxr-xr-x   1 root     root           0 Apr 19 01:32 .SELF-ASSEMBLY-REQUIRED
-rw-------   1 root     root          30 May  5 06:45 .sh_history
lrwxrwxrwx   1 root     root           9 Apr 19 01:32 bin -> ./usr/bin
drwxr-xr-x  65 root     root          15 May  6 11:54 dev
drwxr-xr-x  30 root     root          38 Apr 19 01:32 etc
drwxr-xr-x   2 root     root           2 Apr 19 01:32 export
dr-xr-xr-x   2 root     root           2 Apr 19 01:32 home
drwxr-xr-x   8 root     root         143 Apr 19 01:32 lib
drwxr-xr-x   2 root     root           2 Apr 19 01:32 mnt
drwxr-xr-x   2 root     root           2 Apr 19 01:32 opt
dr-xr-xr-x   4 root     root      480032 May  6 11:54 proc
drwx------   2 root     root           3 Apr 19 01:32 root
lrwxrwxrwx   1 root     root          10 Apr 19 01:32 sbin -> ./usr/sbin
drwxr-xr-x   5 root     root           5 Apr 19 01:32 system
drwxrwxrwt   2 root     root         117 May  6 11:54 tmp
drwxr-xr-x  15 root     root          21 Apr 19 01:32 usr
drwxr-xr-x  18 root     root          19 Apr 19 01:32 var
```

#### Create a container

```
$ sudo oci container create --name mycontainer -w / solaris ls -la
```

#### List containers

```
$ oci container ls
CONTAINER ID   IMAGE            COMMAND   CREATED        STATUS             PORTS   NAMES      
e3893c338624   solaris:latest   ls -la    a minute ago   Created a minute           mycontainer
```


#### Start a container

```
$ sudo oci container start mycontainer
total 1008
drwxr-xr-x  15 root     root          19 Apr 19 01:32 .
drwxr-xr-x  15 root     root          19 Apr 19 01:32 ..
-rwxr-xr-x   1 root     root           0 Apr 19 01:32 .SELF-ASSEMBLY-REQUIRED
-rw-------   1 root     root          30 May  5 06:45 .sh_history
lrwxrwxrwx   1 root     root           9 Apr 19 01:32 bin -> ./usr/bin
drwxr-xr-x  65 root     root          15 May  6 11:54 dev
drwxr-xr-x  30 root     root          38 Apr 19 01:32 etc
drwxr-xr-x   2 root     root           2 Apr 19 01:32 export
dr-xr-xr-x   2 root     root           2 Apr 19 01:32 home
drwxr-xr-x   8 root     root         143 Apr 19 01:32 lib
drwxr-xr-x   2 root     root           2 Apr 19 01:32 mnt
drwxr-xr-x   2 root     root           2 Apr 19 01:32 opt
dr-xr-xr-x   4 root     root      480032 May  6 11:54 proc
drwx------   2 root     root           3 Apr 19 01:32 root
lrwxrwxrwx   1 root     root          10 Apr 19 01:32 sbin -> ./usr/sbin
drwxr-xr-x   5 root     root           5 Apr 19 01:32 system
drwxrwxrwt   2 root     root         117 May  6 11:54 tmp
drwxr-xr-x  15 root     root          21 Apr 19 01:32 usr
drwxr-xr-x  18 root     root          19 Apr 19 01:32 var
```

#### Delete a container

```
$ oci container rm mycontainer
```


