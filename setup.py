#!/usr/bin/env python3
"""
Boneglaive2 Setup Script
Alternative setup using setuptools for easier distribution
"""

from setuptools import setup, find_packages
import sys

# Read requirements
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Platform-specific requirements
install_requires = []
for req in requirements:
    if ';' in req:
        # Handle conditional requirements
        if 'sys_platform == "win32"' in req and sys.platform == 'win32':
            install_requires.append(req.split(';')[0].strip())
        elif 'python_version' in req:
            install_requires.append(req.split(';')[0].strip())
    else:
        install_requires.append(req)

setup(
    name="boneglaive2",
    version="0.8.0c",
    description="Linux & BSD terminal tactical combat game",
    packages=find_packages(),
    install_requires=install_requires,
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'boneglaive2=boneglaive.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: BSD",
        "Topic :: Games/Entertainment :: Turn Based Strategy",
    ],
    keywords="game tactical combat strategy terminal curses nix unix linux bsd",
    include_package_data=True,
)