#!/bin/bash

set -euxo pipefail

rm -f db.sqlite3 frontend.sqlite3
. .env
./venv/bin/python cli.py all --deploy

