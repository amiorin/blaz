from blaz import Blaz


class TestBlaz(object):
    def test_foo(self):
        image = 'pierone.stups.zalan.do/nuggad/jenkins-builder:0.0.17'
        image_next = 'pierone.stups.zalan.do/nuggad/jenkins-builder:0.0.18'
        b = Blaz()
        assert image_next == b._next_docker_image_version(image)

    def test_format(self):
        b = Blaz()
        b.run("echo {0.foo}", format=False)
