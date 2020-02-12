import os
import pathlib
import re
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# Name of the module
MODULE_NAME = 'tfs'

# Dependencies for the module itself
DEPENDENCIES = ['numpy>=1.14.1',
                'pandas>=0.22.0, <1.0'
                ]

# Test dependencies that should only be installed for test purposes
TEST_DEPENDENCIES = ['pytest>=5.2',
                     'pytest-cov>=2.6',
                     'hypothesis>=3.23.0',
                     'attrs>=19.2.0'
                     ]

# pytest-runner to be able to run pytest via setuptools
SETUP_REQUIRES = ['pytest-runner']

# Extra dependencies for tools
EXTRA_DEPENDENCIES = {'doc': ['sphinx',
                              'travis-sphinx',
                              'sphinx_rtd_theme']
                      }

# The text of the README file
README = (HERE / "README.md").read_text()


def get_version():
    """ Reads package version number from package's __init__.py. """
    with open(os.path.join(
        os.path.dirname(__file__), MODULE_NAME, '__init__.py'
    )) as init:
        for line in init.readlines():
            res = re.match(r'^__version__ = [\'"](.*)[\'"]$', line)
            if res:
                return res.group(1)


# This call to setup() does all the work
setup(
    name='tfs-pandas',
    version=get_version(),
    description="Read and write tfs files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/pylhc/tfs",
    author="pyLHC",
    author_email="pylhc@github.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(include=(MODULE_NAME,)),
    install_requires=DEPENDENCIES,
    tests_require=DEPENDENCIES + TEST_DEPENDENCIES,
    extras_require=EXTRA_DEPENDENCIES,
    setup_requires=SETUP_REQUIRES

)
