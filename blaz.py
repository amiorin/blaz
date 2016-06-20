from distutils.spawn import find_executable
from os import environ, chdir, getenv
from os.path import abspath, basename, dirname, join as join_dir
from subprocess import check_call, CalledProcessError
from sys import argv
from colors import bold
from hashlib import md5
from version import __version__
import semantic_version
import sys

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


class Blaz(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.file = abspath(argv[0])
        self.script = basename(self.file)
        self.argv = ' '.join(argv[1:])
        self.__dict__.update({
            'dir': dirname(self.file),
            'image': getenv('BLAZ_IMAGE', 'amiorin/alpine-blaz'),
            'docker_exe': self._find_docker_exe(),
            'docker_sock': getenv('DOCKER_SOCK', '/var/run/docker.sock'),
            'docker_options': getenv('DOCKER_OPTIONS', '--rm --privileged --net=host'),
            'version': __version__
        })
        chdir(self.dir)
        if 'BLAZ_CHDIR_REL' in environ:
            self.mount_dir = abspath(join_dir(self.dir, environ['BLAZ_CHDIR_REL']))
        else:
            self.mount_dir = self.dir
        self._create_lock()

    def _find_latest_docker_image(self):
        image = self.image
        while True:
            prev = image
            image = image.format(self)
            if prev == image:
                break
        self.image = self._do_find_latest_docker_image(image)

    def _do_find_latest_docker_image(self, image):
        next_image = self._next_docker_image_version(image)
        try:
            check_call(['docker', 'pull', next_image], stdout=DEVNULL, stderr=DEVNULL)
        except CalledProcessError:
            return image
        else:
            return self._do_find_latest_docker_image(next_image)

    def _next_docker_image_version(self, image):
        xs = image.split(':')
        assert len(xs) == 2, "Your docker image name ({}) doesn't contain the tag".format(image)
        xs[-1] = str(semantic_version.Version(xs[-1]).next_patch())
        return ':'.join(xs)

    def _find_docker_exe(self):
        if 'DOCKER_EXE' not in environ:
            return find_executable('docker')
        else:
            return environ['DOCKER_EXE']

    def _create_lock(self):
        m = md5()
        m.update(bytearray('{0.dir}/{0.script} {0.argv}'.format(self), 'utf-8'))
        self.lock = m.hexdigest()

    def before(self):
        return not self._fresh()

    def after(self):
        return self._fresh()

    def _fresh(self):
        if 'BLAZ_LOCK' in environ:
            return environ['BLAZ_LOCK'] == self.lock
        else:
            return False

    def invoke(self, main):
        if self._fresh() or 'BLAZ_SKIP' in environ:
            if 'BLAZ_SKIP' in environ:
                del environ['BLAZ_SKIP']
            if 'DOCKER_IMMUTABLE' in environ:
                del environ['DOCKER_IMMUTABLE']
            main(self)
        else:
            if 'DOCKER_IMMUTABLE' not in environ:
                if 'BLAZ_DONT_PULL' not in environ:
                    check_call(['docker', 'pull', "{0.image}".format(self)], stdout=DEVNULL, stderr=DEVNULL)
            else:
                self._find_latest_docker_image()
            self._docker_run()

    def cd(self, subdir="."):
        chdir(join_dir(self.mount_dir, subdir))

    def log(self, msg='', fg='yellow'):
        sys.stdout.flush()
        sys.stderr.write(bold(str(msg) + '\n', fg=fg))
        sys.stderr.flush()

    def run(self, cmd, fg='green'):
        while True:
            prev = cmd
            cmd = cmd.format(self)
            if prev == cmd:
                break
        self.log(cmd, fg=fg)
        check_call(cmd, shell=True)
        sys.stdout.flush()
        sys.stderr.flush()

    def _forward_blaz_env_vars(self):
        result = []
        for k in environ.keys():
            if k.find('BLAZ_') == 0 and k != 'BLAZ_LOCK' and k != 'BLAZ_VERSION' and k != 'BLAZ_CHDIR_REL' and k != 'BLAZ_SKIP':
                result.append('''
  --env={}={}
'''.format(k, environ[k]))
            elif k.find('_BLAZ_') == 0:
                result.append('''
  --env={0}=${0}
'''.format(k))
        return ''.join(result)

    def _docker_run(self):
        cmd = '''
{0.docker_exe} run
  {0.docker_options}
'''
        cmd = cmd + self._forward_blaz_env_vars()
        cmd = cmd + '''
  --env=DOCKER_EXE={0.docker_exe}
  --env=DOCKER_SOCK={0.docker_sock}
  --env=BLAZ_LOCK={0.lock}
  --env=BLAZ_VERSION={0.version}
  --volume={0.mount_dir}:{0.mount_dir}
  --volume={0.docker_exe}:{0.docker_exe}
  --volume={0.docker_sock}:{0.docker_sock}
  {0.image}
  {0.dir}/{0.script} {0.argv}
'''
        cmd = '\n    '.join([x.strip() + ' \\' for x in cmd.split('\n') if
                             x.strip() is not ''])[:-2]
        self.run(cmd, fg='blue')
