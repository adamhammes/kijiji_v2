#!/bin/bash

set -euxo pipefail

. .env
./venv/bin/python cli.py all --deploy --disable-progress

