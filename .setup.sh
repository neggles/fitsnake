#!/usr/bin/env bash

echo "Setting up fitsnake repo in $(pwd)"
git init
git add .
git commit --quiet --message "Initial commit"
git tag v0.0.1

echo "Creating python virtualenv"
/usr/bin/env python3 -m virtualenv .venv
source .venv/bin/activate

echo "Updating pip and setuptools"
pip install --upgrade --quiet pip setuptools wheel setuptools-scm

echo "Installing package in dev mode..."
pip install --editable '.[dev]'
python -m setuptools_scm

exit 0
