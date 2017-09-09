import os
from setuptools import find_packages, setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='pysonyavr',
    version='1.0',
    license='GPL3',
    description='Python bindings for modern Sony speakers',
    long_description=read('README.rst'),
    author='Philipp Schmitt',
    author_email='philipp@schmitt.co',
    url='https://github.com/pschmitt/pysonyavr',
    packages=find_packages(),
    install_requires=['requests'],
)
