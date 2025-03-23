#!/usr/bin/env python3
from pathlib import Path

import setuptools
from setuptools import setup

this_dir = Path(__file__).parent

requirements = []
requirements_path = this_dir / "requirements.txt"
if requirements_path.is_file():
    with open(requirements_path, "r", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read().splitlines()

# Setup details for the new module (v3)
module_name = "wyoming_porcupine3"
module_dir = this_dir / module_name
version_path = module_dir / "VERSION"
version = version_path.read_text(encoding="utf-8").strip()

# -----------------------------------------------------------------------------

setup(
    name=module_name,
    version=version,
    description="Wyoming Server for Porcupine 3",
    url="http://github.com/rhasspy/wyoming-porcupine",
    author="Michael Hansen",
    author_email="mike@rhasspy.org",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={module_name: ["VERSION"]},
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="rhasspy wyoming porcupine wake word",
    entry_points={
        "console_scripts": ["wyoming-porcupine3 = wyoming_porcupine3.__main__:run"]
    },
)
