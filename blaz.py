from distutils.spawn import find_executable
from os import environ, chdir, getenv, getuid, getgid
from os.path import abspath, basename, dirname, join as join_dir
from subprocess import check_call, CalledProcessError
from sys import argv
from colors import bold
from hashlib import md5
from version import __version__
import sys
import re


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
        self.mount_dir = "/".join(self.dir.split("/")[0:3])
        if 'BLAZ_CHDIR_REL' in environ:
            self.project_dir = abspath(join_dir(self.dir, environ['BLAZ_CHDIR_REL']))
        else:
            self.project_dir = self.dir
        self._create_lock()

    def _find_uid_and_guid(self):
        if 'BLAZ_UID' not in environ:
            environ['BLAZ_UID'] = str(getuid())
            environ['BLAZ_GID'] = str(getgid())

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
            main(self)
        else:
            if 'BLAZ_DONT_PULL' not in environ:
                check_call("docker pull {0.image}".format(self), shell=True)
            self._docker_run()

    def cd(self, subdir="."):
        chdir(join_dir(self.project_dir, subdir))

    def log(self, msg='', fg='yellow'):
        sys.stdout.flush()
        sys.stderr.write(bold(str(msg) + '\n', fg=fg))
        sys.stderr.flush()

    def run(self, cmd, fg='green', format=True):
        if format:
            while True:
                prev = cmd
                cmd = cmd.format(self)
                if prev == cmd:
                    break
        self.log(cmd, fg=fg)
        try:
            check_call(cmd, shell=True)
        except CalledProcessError as ex:
            self.log('\n' + str(ex), fg='red')
            sys.exit(1)
        finally:
            sys.stdout.flush()
            sys.stderr.flush()

    def _forward_blaz_env_vars(self):
        self._find_uid_and_guid()
        result = []
        for k in environ.keys():
            if k.find('BLAZ_') == 0 and k != 'BLAZ_LOCK' and k != 'BLAZ_VERSION' and k != 'BLAZ_CHDIR_REL' and k != 'BLAZ_SKIP':
                result.append('''
  --env={}="{}"
'''.format(k, environ[k]))
                if k.find('BLAZ_VARS') == 0:
                    env_vars = re.split('\W+', environ[k])
                    for j in env_vars:
                        result.append('''
  --env={}="{}"
'''.format(j, environ[j]))
            elif k.find('_BLAZ_') == 0:
                result.append('''
  --env={0}="${0}"
'''.format(k))
                if k.find('_BLAZ_VARS') == 0:
                    env_vars = re.split('\W+', environ[k])
                    for j in env_vars:
                        result.append('''
  --env={0}="${0}"
'''.format(j))
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
  "{0.dir}/{0.script}" {0.argv}
'''
        cmd = '\n    '.join([x.strip() + ' \\' for x in cmd.split('\n') if
                             x.strip() is not ''])[:-2]
        self.run(cmd, fg='blue')
