import hypnogen


def test_package_version():
    assert hypnogen.__version__ == "0.1.0"


def test_basic_assertion():
    assert 1 + 1 == 2
