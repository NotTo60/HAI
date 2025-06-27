from setuptools import setup, find_packages

setup(
    name="hai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "paramiko>=2.7.0",
        "impacket>=0.9.0",
        "pytest>=6.0.0",
        "pyyaml>=5.0",
        "cryptography>=3.0",
        "bcrypt>=3.0",
        "pynacl>=1.0",
    ],
    python_requires=">=3.8",
    description="HAI - Host Access Infrastructure",
    author="HAI Team",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
) 