## Intro
Blaz runs your scripts inside docker.

## Why
With blaz you can create docker images with all the dependencies of your script like python3, ansible, aws cli, terraform, puppet, chef, make, go...

## Requirements
* docker-machine (dinghy works out of the box) or a **static** version of docker
* **nfs** (better) or vboxsf (you could have stale scripts) in OSX
* a **docker image** with python3 and blaz

### docker-machine
[dinghy](https://github.com/codekitchen/dinghy) works out of the box.

### Quick start
```
# blaz is not yet in pypi registry.
pip3 install .
# Docker image with python3 and blaz
docker build -t alpine-blaz .
# blaz script example
./run
```

## Environment variables
These are the defaults that you can override
```sh
# docker-machine
DOCKER_EXE=/usr/local/bin/docker
# docker installed with the debian package
DOCKER_EXE=/usr/bin/docker
DOCKER_SOCK=/var/run/docker.sock
# docker image to start your script
BLAZ_IMAGE=alpine-blaz
```

All environment variables like ``BLAZ_*`` and ``_BLAZ_*`` are forwarded to the next container. The former are printed the latter are not (useful for secrets like AWS credentials inside jenkins).

## Nested scripts
A blaz script can invoke another blaz script. A new docker container will be used for the nested script.

## Blaz api
* blaz.invoke
* blaz.run
* blaz.log

## Use cases
* jenkins
* ansible
* build docker images

### Build docker images
You can split compile and build. For example you can create a script that
1. compile your go source code with alpine + blaz + go (220 MB)
2. build alpine docker with the static go executable (5 MB + your go program)
3. push to the docker container registry

### Ansible
```python
#!/usr/bin/env python3

from blaz import Blaz

def task(blaz):
    blaz.log('## Provisioning AWS ##')
    blaz.run('PYTHONUNBUFFERED=1 ansible site.yml')
    # this will start a fresh container, after ansible is done
    blaz.run('../other_blaz_script.py')

if __name__ == "__main__":
    # the task function will be invoke in a fresh container
    Blaz().invoke(task)
```
