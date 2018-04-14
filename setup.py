from codecs import open
from os import path

from setuptools import find_packages
from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='minitor',
    version='0.1.3',
    description='A minimal monitoring tool',
    long_description=long_description,
    url='https://git.iamthefij.com/iamthefij/minitor',
    download_url=(
        'https://git.iamthefij.com/iamthefij/minitor/archive/master.tar.gz'
    ),
    author='Ian Fijolek',
    author_email='ian@iamthefij.com',
    classifiers=[
        # How mature is this project? Common values are
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='minitor monitoring alerting',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'yamlenv',
    ],
    entry_points={
        'console_scripts': [
            'minitor=minitor.main:main',
        ],
    },
)
