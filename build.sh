#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

if [ -f "seed_data.json" ]; then
    echo "Loading initial database fixtures..."
    python manage.py loaddata seed_data.json || true
fi
