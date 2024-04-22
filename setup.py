#!/usr/bin/env python3.11
"""Setup the package."""
import setuptools

setuptools.setup(
    name="shortcake",
    version="0.1",
    description="A private Gdk library",
    url="#",
    author="midnattssol",
    install_requires=["numpy", "pycairo", "more_itertools", "colour", "nerdfonts_patched"],
    author_email="",
    packages=setuptools.find_packages(),
    zip_safe=False,
)
