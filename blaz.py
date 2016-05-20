from distutils.spawn import find_executable
from os import environ, chdir, getenv
from os.path import abspath, basename, dirname
from subprocess import check_call
from sys import argv
from colors import bold
from hashlib import md5
from version import __version__
import sys


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
        self._create_lock()

    def _find_docker_exe(self):
        if 'DOCKER_EXE' not in environ:
            return find_executable('docker')
        else:
            return environ['DOCKER_EXE']

    def _create_lock(self):
        m = md5()
        m.update(bytes('{0.dir}/{0.script} {0.argv}'.format(self), 'utf-8'))
        self.lock = m.hexdigest()

    def _fresh(self):
        if 'BLAZ_LOCK' in environ:
            return environ['BLAZ_LOCK'] == self.lock
        else:
            return False

    def invoke(self, main):
        if self._fresh():
            main(self)
        else:
            self._docker_run()

    def log(self, msg='', fg='yellow'):
        sys.stdout.flush()
        sys.stderr.write(bold(msg + '\n', fg=fg))
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
            if k.find('BLAZ_') == 0 and k != 'BLAZ_LOCK' and k != 'BLAZ_VERSION':
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
  --volume={0.dir}:{0.dir}
  --volume={0.docker_exe}:{0.docker_exe}
  --volume={0.docker_sock}:{0.docker_sock}
  {0.image}
  {0.dir}/{0.script} {0.argv}
'''
        cmd = '\n    '.join([x.strip() + ' \\' for x in cmd.split('\n') if
                             x.strip() is not ''])[:-2]
        self.run(cmd, fg='blue')
