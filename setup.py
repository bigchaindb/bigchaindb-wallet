#!/usr/bin/env python3
from setuptools import setup

setup(
    name="bigchaindb-wallet",
    version="0.0.1",
    author="David Dashyan",
    author_email="mail@davie.li",
    description="Deterministic wallet implementation for BigchainDB",
    long_description=open("README.md").read(),
    url="https://github.com/bigchaindb/bigchaindb_wallet",
    packages=["bigchaindb_wallet"],
    py_modules=[
        "bigchaindb_wallet.keystore",
        "bigchaindb_wallet._cli"
    ],
    install_requires=[
        "Click",
        "pickledb",
        "PyNaCl",
        "bigchaindb_driver",
        "mnemonic",
    ],
    entry_points='''
        [console_scripts]
        bdbw=bigchaindb_wallet._cli:cli
    ''',
    tests_require=[
        "hypothesis",
        "pytest",
        "pytest-httpserver",
        "schema",
    ],
    zip_safe=False,
    python_requires=">=3.5",
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
)
