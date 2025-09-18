#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput
