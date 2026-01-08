"""
Cirkelline CLI Setup
====================
Installation script for Cirkelline Terminal CLI.

Install:
    pip install -e ./cli

Usage after install:
    cirkelline --help
    cirkelline login
    cirkelline status
    cirkelline ask "What is..."
"""

from setuptools import setup, find_packages

setup(
    name="cirkelline-cli",
    version="1.0.0",
    description="Cirkelline Terminal CLI - Kommandant Interface",
    author="Cirkelline Team",
    author_email="team@cirkelline.com",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "cirkelline=cli.main:main",
            "ckl=cli.main:main",  # Short alias
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
