#!/bin/bash
pip install pipenv || exit 1

rm -rf ../stylesheets/inline/critical
mkdir ../stylesheets/inline/critical

pipenv install || exit 2

pipenv run python -m pytest -vv || exit 3
pipenv run python compile.py || exit 4

node build-critical-css.js || exit 5

echo '------> Rerun .journal complilation to include inline css'
pipenv run python compile.py || exit 6
