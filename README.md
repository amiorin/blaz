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
```sh
git clone https://github.com/amiorin/blaz
cd blaz
pip3 install blaz
./run
```
![screenshot](https://raw.githubusercontent.com/amiorin/blaz/master/blaz.png)

## Environment variables
These are the defaults that you can override
```sh
# DOCKER_EXE is now optional
# docker-machine
DOCKER_EXE=/usr/local/bin/docker
# docker installed with the debian package
DOCKER_EXE=/usr/bin/docker
DOCKER_SOCK=/var/run/docker.sock
DOCKER_OPTIONS="--rm --privileged --net=host"
# docker image to start your script
BLAZ_IMAGE=amiorin/alpine-blaz
# to change the mount point with a relative path starting from the directory containing the script
BLAZ_CHDIR_REL=../..
# to skip the docker run step
BLAZ_SKIP=1
```

All environment variables like ``BLAZ_*`` and ``_BLAZ_*`` are forwarded to the next container. The former are printed the latter are not (useful for secrets like AWS credentials inside jenkins).

## Reserved env variables
``BLAZ_LOCK``, ``BLAZ_VERSION``, ``BLAZ_SKIP`` and ``BLAZ_CHDIR_REL`` are reserved.

Env var | Explanation
---|---
BLAZ_LOCK | It's the digest of the fullpath of the script and it's used to understand if we need to start a new ``docker run``
BLAZ_VERSION | For debugging purpose, it's the blaz version inside the container
BLAZ_SKIP | When you want to compose two blaz scripts but you don't want to start two different containers
BLAZ_CHDIR_REL | When the script has to access to files that are not under his directory but somewhere else. It allows mount a volume that is different from the directory of the current script using a relative path like ``../..``
DOCKER_OPTIONS | To override ``--rm --privileged --net=host``
DOCKER_EXE | To specify a the docker executable when you have multiple versions
DOCKER_SOCK | To override the ``var/run/docker.sock``

## Nested scripts
A blaz script can invoke another blaz script. A new docker container will be used for the nested script, unless you define the environment variable ``BLAZ_SKIP``.

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

## Publish

```
python setup.py sdist
twine upload dist/*
docker build --no-cache -t amiorin/alpine-blaz .
docker push amiorin/alpine-blaz
docker tag ...
docker push ...
```

## Development
* Install pyenv

```
pip install -e .
```
