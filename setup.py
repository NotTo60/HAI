from setuptools import setup, find_packages

setup(
    name="hai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "paramiko",
        "impacket",
        "pytest",
    ],
    python_requires=">=3.8",
) 