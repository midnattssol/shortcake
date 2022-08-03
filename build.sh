#!/bin/sh
set -eux pipefail

pybuild pybuild.cson
pip install .
