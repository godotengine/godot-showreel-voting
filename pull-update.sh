#!/usr/bin/env bash
set -euo pipefail

# Allow running this script from any directory
script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${script_dir}"

# Update the application
git pull
source ./venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
deactivate

# Restart apache
systemctl restart apache2.service

# Restore work directory
popd
