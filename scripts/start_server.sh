#!/bin/sh
script_dir=$(dirname "$(readlink -f "$0")")
export KB_DEPLOYMENT_CONFIG=$script_dir/../deploy.cfg
export PYTHONPATH=$script_dir/../lib:$PYTHONPATH
uwsgi --plugins http,python --master --processes 5 --threads 5 --http :5000 --wsgi-file $script_dir/../lib/combinatrix/CombinatrixServer.py
