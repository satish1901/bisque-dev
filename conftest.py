import os


def load_config(filename):
    # setup resources before any test is executed
    from paste.deploy import appconfig
    from bq.config.environment import load_environment
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

# content of conftest.py
def pytest_sessionstart():
    print "PYTEST START"
    load_config ("config/test.ini")


def pytest_sessionfinish():
    # teardown resources after the last test has executed
    print "PYTEST END"
