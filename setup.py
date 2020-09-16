import pathlib

import setuptools

# The directory containing this file
TOPLEVEL_DIR = pathlib.Path(__file__).parent.absolute()
ABOUT_FILE = TOPLEVEL_DIR / "tfs" / "__init__.py"
README = TOPLEVEL_DIR / "README.md"

with README.open("r") as docs:
    long_description = docs.read()

MODULE_NAME = "tfs"

# Dependencies for the package itself
DEPENDENCIES = [
    "numpy>=1.17.4",
    "pandas>=1.0",
]

# Extra dependencies
EXTRA_DEPENDENCIES = {
    "test": ["pytest>=5.2", "pytest-cov>=2.7",],
    "doc": ["sphinx", "travis-sphinx", "sphinx_rtd_theme"],
}
EXTRA_DEPENDENCIES.update(
    {"all": [elem for list_ in EXTRA_DEPENDENCIES.values() for elem in list_]}
)

setuptools.setup(
    name="tfs-pandas",
    version="2.0.0",
    description="Read and write tfs files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="pyLHC",
    author_email="pylhc@github.com",
    url="https://github.com/pylhc/tfs",
    packages=setuptools.find_packages(include=(MODULE_NAME,)),
    include_package_data=True,
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=DEPENDENCIES,
    tests_require=EXTRA_DEPENDENCIES["test"],
    extras_require=EXTRA_DEPENDENCIES,
)
