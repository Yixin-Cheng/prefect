import base64
from configparser import ConfigParser
import hashlib
import logging
import os
import re

env_var_re = re.compile(
    '^PREFECT__(?P<section>\S+)__(?P<option>\S+)', re.IGNORECASE)


def call_fn(fn):
    """
    Simple decorate that calls a function automatically, allowing configuration
    variables to be placed inside functions instead of polluting the namespace
    """
    fn()
    return fn


def expand(env_var):
    """
    Expands (potentially nested) env vars by repeatedly applying
    `expandvars` and `expanduser` until interpolation stops having
    any effect.
    """
    if not env_var:
        return env_var
    while True:
        interpolated = os.path.expanduser(os.path.expandvars(str(env_var)))
        if interpolated == env_var:
            return interpolated
        else:
            env_var = interpolated


def load_config(test_mode=False, config_file=None, home=None):
    """
    Loads a new Prefect configuration.

    If the env var PREFECT__CORE__CONFIG or config_file is passed,
    configuration is loaded from that location. Otherwise,
    PREFECT__CORE__PREFECT_DIR and prefect_dir are checked for an existing
    configuration. Lastly, if no configuration exists, a new one is generated
    at the specified location.
    """

    test_mode = os.getenv('PREFECT__CORE__TEST_MODE', test_mode)

    home = os.getenv('PREFECT__CORE__HOME', home)
    if home is None:
        home = '~/.prefect'
    home = expand(home)

    config_file = os.getenv('PREFECT__CORE__CONFIG', config_file)
    if config_file is None:
        config_file = os.path.join(home, 'prefect.cfg')
    config_file = expand(config_file)

    default_config_file = os.path.join(
        os.path.dirname(__file__), 'config_templates', 'prefect.cfg')
    test_config_file = os.path.join(
        os.path.dirname(__file__), 'config_templates', 'tests.cfg')

    os.makedirs(home, exist_ok=True)

    if not os.path.isfile(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(default_config_file, 'r') as fr:
            with open(config_file, 'w') as fw:
                fw.write(fr.read())

    config = ConfigParser()
    with open(default_config_file, 'r') as f:
        config.read_file(f)
    # If we're in test mode, read test config. Otherwise read user config.
    if test_mode:
        with open(test_config_file, 'r') as f:
            config.read_file(f)
    else:
        with open(config_file, 'r') as f:
            config.read_file(f)

    # overwrite environment variables
    for ev in os.environ:
        match = re.match(env_var_re, ev)
        if match:
            config.set(
                section=match.groupdict()['section'].lower(),
                option=match.groupdict()['option'].lower(),
                value=os.environ[ev])

    return config


config = load_config()

# Test Mode -------------------------------------------------------------------

if config.get('core', 'test_mode'):
    config = load_config(test_mode=True)

# Logging ---------------------------------------------------------------------

@call_fn
def configure_logging():
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(config.get('logging', 'format'))
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, config.get('logging', 'level')))


# Database --------------------------------------------------------------------

@call_fn
def configure_database():
    # hash the secret key
    key = config.get(section='db', option='secret_key').encode()
    hashed_key = hashlib.sha256(key).digest()
    config.set(
        section='db',
        option='secret_key',
        value=base64.b64encode(hashed_key).decode())
