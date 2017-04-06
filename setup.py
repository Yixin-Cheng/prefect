from setuptools import setup, find_packages

install_requires = [
    'croniter',
    'dask',
    'distributed',
    'hug',
    'pycrypto',
    'pendulum',
    'sqlalchemy',
    'transitions',
]

extras = {
    's3': ['awsfs'],
    # 'gcs': ['https://github.com/martindurant/gcsfs.git'],
    'test': ['pytest', 'pytest-env', 'pytest-xdist'],
}

setup(
    name='prefect-flow',
    version='0.0',
    description='',
    long_description=open('README.md').read(),
    url='https://gitlab.com/prefect/prefect',
    author='jlowin',
    author_email='jlowin@apache.org',
    install_requires=install_requires,
    extras_require=extras,
    scripts=[],
    packages=find_packages(),
    include_package_data=True,)
