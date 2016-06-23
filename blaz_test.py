from blaz import Blaz


class TestBlaz(object):
    def test_format(self):
        b = Blaz()
        b.run("echo {0.foo}", format=False)
